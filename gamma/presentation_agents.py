"""
Presentation generation using agent orchestration pattern (no workflow).

This module uses agents with the "agent as tool" pattern:
- Orchestrator Agent: dispatches work to other agents in succession
- Outline Agent: creates presentation outline (available as tool)
- Researcher Agent: researches and creates slide content (available as tool)
- Reviewer Agent: reviews and finalizes the presentation (available as tool)
- Gamma API: generates the final PDF presentation using output from the orchestrator (structured output)
"""

import asyncio
import json
import logging
import os
from typing import Annotated, Awaitable
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from collections.abc import Callable

from config.config import (
    API_KEY as GAMMA_API_KEY,
    API_BASE_URL as GAMMA_API_BASE_URL,
    AZURE_OPENAI_ENDPOINT as endpoint,
    AZURE_OPENAI_API_KEY as api_key,
    AZURE_OPENAI_DEPLOYMENT as deployment_name,
)

from agent_framework import (
    ai_function,
    FunctionInvocationContext,
)
from agent_framework.azure import AzureOpenAIResponsesClient
from agent_framework.devui import serve

from tools.search import search_web
from gamma_api import GammaAPIClient

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Custom formatter to show only filename, not full path
class ShortFileFormatter(logging.Formatter):
    def format(self, record):
        record.pathname = record.filename
        return super().format(record)

# Update root logger with custom formatter
root_logger = logging.getLogger()
for log_handler in root_logger.handlers:
    log_handler.setFormatter(
        ShortFileFormatter(
            '[%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    )

# logging function middleware
async def logging_function_middleware(
    context: FunctionInvocationContext,
    next: Callable[[FunctionInvocationContext], Awaitable[None]],
) -> None:
    """Middleware that logs function calls."""
    logger.info(f'FUNCTION - "{context.function.name}" - Invoked')

    await next(context)

    result_preview = str(context.result)[:100].replace('\n', ' ')
    logger.info(f'FUNCTION - "{context.function.name}" - Result: {result_preview}')


# Pydantic models for agent responses
class SlideTitle(BaseModel):
    title: str
    reason: str

class OutlineResponse(BaseModel):
    title: str
    number_of_slides: Annotated[int, Field(default=5, description="Number of slides in the presentation")]
    slide_titles: list[SlideTitle]
    audience: Annotated[str, Field(default="general", description="Single word target audience for the presentation (technical, business, ...)")]

class SlideContent(BaseModel):
    title: str
    content: str

class ResearchResponse(BaseModel):
    title: str
    number_of_slides: int
    slides: list[SlideContent]
    audience: Annotated[str, Field(default="general", description="Single word target audience for the presentation (technical, business, ...)")]

class ReviewResponse(BaseModel):
    title: str
    number_of_slides: int
    slides: list[SlideContent]
    notes: Annotated[list[str], Field(description="Highly detailed slide notes for the presenter, providing in-depth guidance, key talking points, and additional context for each slide to ensure effective delivery.")]
    audience: str
    review_notes: str
    is_final: bool = True


class OrchestratorOutput(BaseModel):
    """Structured output from the orchestrator containing final reviewed presentation data."""
    title: Annotated[str, Field(description="Presentation title from reviewer agent")]
    number_of_slides: Annotated[int, Field(description="Number of slides from reviewer agent")]
    slides: Annotated[list[SlideContent], Field(description="Final slide content from reviewer agent")]
    notes: Annotated[list[str], Field(description="Highly detailed slide notes for the presenter, providing in-depth guidance, key talking points, and additional context for each slide to ensure effective delivery.")]
    audience: Annotated[str, Field(description="Target audience from reviewer agent")]
    review_notes: Annotated[str, Field(description="Review notes and feedback from reviewer agent")]
    is_final: Annotated[bool, Field(description="Whether the presentation is final and ready for generation")]


# Create individual agents

# Outline Agent - creates presentation outline
outline_agent = AzureOpenAIResponsesClient(
    endpoint=endpoint,
    api_key=api_key,
    deployment_name=deployment_name
).create_agent(
    name="OutlineAgent",
    instructions="""
        Based on the user's request, you create an outline for a presentation.
        Generate a title for the presentation and a list of slide titles.
        If the user specified a number of slides, use that number.
        Before you generate the outline, use the 'search_web' tool to research the topic thoroughly with ONE query.
        Base the outline on the research findings.
    """,
    tools=[search_web],
    response_format=OutlineResponse,
    middleware=[logging_function_middleware]
)

# Research Agent - researches and creates slide content
research_agent = AzureOpenAIResponsesClient(
    endpoint=endpoint,
    api_key=api_key,
    deployment_name=deployment_name
).create_agent(
    name="ResearchAgent",
    instructions="""
        You research and create content for slides. You will receive a presentation
        title and a list of slide titles with the reason the title was chosen.
        Generate two web search queries to gather information for each slide title.
        Keep in mind the target audience when generating the queries.
        Next, use the 'search_web' tool ONCE passing in the queries all at once.

        Use the result from the queries to generate content for each slide. 
        Content for slides should be limited to 100 words max with three main bullet points.
        If you require an extra slide (max 3 extra), to explain a complex topic, feel free to add it.
        Ensure you update the number_of_slides field accordingly.
    """,
    tools=[search_web],
    response_format=ResearchResponse,
    kwargs={"verbosity": "high"},
    middleware=[logging_function_middleware]
)

# Reviewer Agent - reviews and finalizes the presentation
reviewer_agent = AzureOpenAIResponsesClient(
    endpoint=endpoint,
    api_key=api_key,
    deployment_name=deployment_name
).create_agent(
    name="ReviewerAgent",
    instructions="""
        You are a presentation quality reviewer. You will receive research data about a presentation.
        
        Your tasks:
        1. Review the slide titles and content for clarity, coherence, and alignment
        2. Check that content is appropriately detailed for the target audience
        3. Never assume audience knows acronyms or specialized terms, even when the audience is technical
        4. Ensure each slide has meaningful content (100 words max with 3 main bullet points)
        5. Provide improvement suggestions in the review_notes field if needed
        6. Ensure you add detailed slide notes. You can use the web search tool to do this if needed.
        7. Return the data in the same structure, marking is_final as True when ready for presentation generation

        Focus on:
        - Content quality and accuracy
        - Appropriate level of detail for the audience
        - Logical flow between slides
        - Consistency in formatting and messaging

        You can use the web search tool 'search_web' to fact-check any information if needed.

        If the subject cannot be covered well in the amount of slides, add max 3 extra slides.
        
        If you find any issues that need fixing, set is_final to False and provide specific notes.
        Otherwise, set is_final to True indicating the presentation is ready.
    """,
    response_format=ReviewResponse,
    tools=[search_web],
    middleware=[logging_function_middleware]
)

# Gamma API Client for presentation generation
def create_gamma_client() -> GammaAPIClient:
    """Create and return a configured Gamma API client."""
    return GammaAPIClient(
        api_key=GAMMA_API_KEY or "",
        api_base_url=GAMMA_API_BASE_URL or "",
        text_mode="condense",
        text_amount="brief",
        text_tone="professional, engaging, informative",
        theme_name="Gamma",
    )


async def generate_presentation_from_content(orchestrator_output: OrchestratorOutput) -> dict:
    """Generate the final PDF presentation using the Gamma API from orchestrator output."""
    logger.info(f'MAIN - Generating presentation with Gamma API: "{orchestrator_output.title}"')
    
    try:
        # Convert orchestrator output to JSON string for Gamma API
        content_dict = orchestrator_output.model_dump()
        content_json_str = json.dumps(content_dict, indent=2)
        
        # Save the content for debugging
        with open(f"{orchestrator_output.title.replace(' ', '_')}_final_content.json", "w") as f:
            f.write(content_json_str)
        
        # Create Gamma API client and generate presentation
        gamma_client = create_gamma_client()
        
        result = await gamma_client.create_presentation(
            input_text=content_json_str,
            number_of_slides=orchestrator_output.number_of_slides,
            audience=orchestrator_output.audience,
            title=orchestrator_output.title,
        )
        
        logger.info(f'MAIN - Presentation generated successfully: {result["pdf_path"]}')
        
        return {
            "success": True,
            "generation_id": result["generation_id"],
            "pdf_url": result["pdf_url"],
            "pdf_path": result["pdf_path"],
        }
        
    except Exception as e:
        logger.error(f'MAIN - Error generating presentation: {str(e)}')
        return {
            "success": False,
            "error": str(e)
        }


# Create the Orchestrator Agent
orchestrator_agent = AzureOpenAIResponsesClient(
    endpoint=endpoint,
    api_key=api_key,
    deployment_name=deployment_name
).create_agent(
    name="OrchestratorAgent",
    instructions="""
        You are the orchestrator for presentation generation. Your job is to coordinate the creation 
        of a professional presentation by delegating tasks to specialized agents.
        
        WORKFLOW - Execute these steps in EXACT order:
        
        1. OUTLINE PHASE: Use the OutlineAgent tool with the user's topic to create the presentation outline
           - Wait for the outline agent to complete
           - The outline includes title, number of slides, slide titles, and target audience
        
        2. RESEARCH PHASE: Use the ResearchAgent tool with the outline from step 1
           - Wait for the researcher agent to complete
           - The researcher creates detailed content for each slide
        
        3. REVIEW PHASE: Use the ReviewerAgent tool with the research data from step 2
           - Wait for the reviewer agent to complete
           - The reviewer validates quality and provides final content
        
        IMPORTANT INSTRUCTIONS:
        - Execute phases in STRICT sequential order - do NOT skip steps
        - Always pass the FULL output from one agent to the next agent's tool
        - Wait for each tool to complete before calling the next one
        - Do NOT modify or summarize the data between agents - pass it as-is
        - Provide clear status updates to the user at each phase
        - Return the FINAL REVIEW DATA from the ReviewerAgent to the user
        
        When the user provides a presentation topic, start with phase 1 immediately.
        After the reviewer completes, return the final reviewed content data.
    """,
    tools=[
        outline_agent.as_tool(),
        research_agent.as_tool(),
        reviewer_agent.as_tool(),
    ],
    response_format=OrchestratorOutput,
    middleware=[logging_function_middleware]
)


async def main():
    """Main function to run the presentation agent orchestrator."""
    print("\n" + "="*70)
    print("🎯 PRESENTATION GENERATION AGENT ORCHESTRATOR")
    print("="*70)
    print("\nThis system uses AI agents working together to create presentations:")
    print("  1. Outline Agent - Creates presentation structure")
    print("  2. Researcher Agent - Creates detailed slide content")
    print("  3. Reviewer Agent - Validates and finalizes content")
    print("  4. Gamma API - Generates the PDF presentation")
    print("\nThe Orchestrator Agent coordinates all agents in sequence.")
    print("\n" + "-"*70 + "\n")
    
    thread = orchestrator_agent.get_new_thread()
    
    print("💬 Chat Mode with Agent Orchestration")
    print("Type your presentation topic and the agents will create it!")
    print("Type '/exit' to end the session.\n")
    
    try:
        while True:
            try:
                # Get user input
                user_input = input("📝 Your topic: ").strip()
                
                # Check for exit command
                if user_input.lower() == '/exit':
                    print("\n👋 Goodbye! Thanks for using the Presentation Generator!")
                    break
                
                if not user_input:
                    continue
                
                print("\n🤖 Orchestrator: ", end="", flush=True)
                
                # Run the orchestrator agent with streaming and capture full response
                orchestrator_response_text = ""
                async for chunk in orchestrator_agent.run_stream(user_input, thread=thread):
                    if chunk.text:
                        print(chunk.text, end="", flush=True)
                        orchestrator_response_text += chunk.text
                
                print("\n")  # New line after streaming
                
                # After orchestrator completes, generate the presentation
                if orchestrator_response_text.strip():
                    try:
                        # Parse the orchestrator's structured output
                        # The orchestrator returns OrchestratorOutput in JSON format
                        orchestrator_output = OrchestratorOutput.model_validate_json(orchestrator_response_text)
                        
                        # Check if number of slides is valid
                        if orchestrator_output.number_of_slides <= 0:
                            print(f"\n⚠️  Cannot generate presentation: Invalid number of slides ({orchestrator_output.number_of_slides})")
                            print("   The orchestrator must create at least 1 slide.\n")
                            continue
                        
                        print("\n📊 Generating PDF presentation...")
                        result = await generate_presentation_from_content(orchestrator_output)
                        
                        if result.get("success"):
                            print(f"\n✅ Presentation generated successfully!")
                            print(f"   Generation ID: {result['generation_id']}")
                            print(f"   PDF URL: {result['pdf_url']}")
                            print(f"   Saved to: {result['pdf_path']}\n")
                        else:
                            print(f"\n⚠️  Could not generate presentation: {result.get('error', 'Unknown error')}\n")
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse orchestrator output as JSON: {e}")
                        print(f"\n⚠️  Failed to parse presentation data: {e}\n")
                    except Exception as e:
                        logger.error(f"Error generating presentation: {e}")
                        print(f"\n⚠️  Error generating presentation: {e}\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Thanks for using the Presentation Generator!")
                break
            except Exception as e:
                logger.error(f"Error in orchestrator: {e}")
                print(f"\n❌ Error: {e}\n")
                continue
                
    finally:
        print("🧹 Cleaning up...")
        print("✅ Session completed")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure you have:")
        print("1. Set up your .env file with Azure OpenAI and Gamma API credentials")
        print("2. Installed the required packages: pip install -r requirements.txt")
        print("3. Authenticated with Azure CLI: az login (if using Azure CLI credentials)")
