# Copyright (c) Microsoft. All rights reserved.

import asyncio

from agent_framework import AgentRunUpdateEvent, WorkflowBuilder, WorkflowOutputEvent
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class MessageData(BaseModel):
    sender: str
    full_message: str
    questions: list[str]

def create_workflow():
    """Build and run a simple two node agent workflow: Writer then Reviewer."""
    # Create the Azure chat client. AzureCliCredential uses your current az login.
    chat_client = AzureOpenAIChatClient(credential=AzureCliCredential())

    # Define two domain specific chat agents.
    classify_agent = chat_client.create_agent(
        instructions=(
            "You excel in extracting sender, full message and a list of questions in the message."
        ),
        name="classify_agent",
        response_format=MessageData

    )

    response_agent = chat_client.create_agent(
        instructions=(
            "Based on your context, write a response that ansers all questions asked. Address the sender politely."
            "If the questions contain profanity, respond that you cannot help with that."
        ),
        name="response_agent",
    )

    # Build the workflow using the fluent builder.
    # Set the start node and connect an edge from writer to reviewer.
    # Agents adapt to workflow mode: run_stream() for incremental updates, run() for complete responses.
    workflow = (
        WorkflowBuilder()
        .set_start_executor(classify_agent)
        .add_edge(classify_agent, response_agent)
        .build()
    )

    return workflow



if __name__ == "__main__":
    workflow = create_workflow()
    from agent_framework.devui import serve

    serve(entities=[workflow], port=8093, auto_open=True)