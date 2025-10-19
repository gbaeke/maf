import asyncio
import os
from dotenv import load_dotenv
from agent_framework.azure import AzureOpenAIResponsesClient
from agent_framework import ai_function
from azure.identity import AzureCliCredential
import aiohttp
from typing import Annotated
from pydantic import Field


# Load environment variables from .env file
load_dotenv()

@ai_function(name="get_weather", description="Get current weather for a given location")
async def get_weather(location: Annotated[str, Field(description="The location to get the weather for.")],
) -> str:
    try:
        # First, geocode the location to get latitude and longitude
        print(f"🌤️ Retrieving weather information for {location}...")
        geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1&language=en&format=json"
        async with aiohttp.ClientSession() as session:
            async with session.get(geocode_url) as response:
                if response.status != 200:
                    return f"Could not geocode location '{location}'. Please check the location name."
                geocode_data = await response.json()
                if not geocode_data.get('results'):
                    return f"Location '{location}' not found. Please check the location name."
                lat = geocode_data['results'][0]['latitude']
                lon = geocode_data['results'][0]['longitude']
        
        # Now, get the weather data
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&temperature_unit=celsius&windspeed_unit=kmh"
        async with aiohttp.ClientSession() as session:
            async with session.get(weather_url) as response:
                if response.status != 200:
                    return f"Could not retrieve weather data for {location}."
                weather_data = await response.json()
                current = weather_data['current_weather']
                temp = current['temperature']
                windspeed = current['windspeed']
                weather_code = current['weathercode']
                
                # Simple weather description based on weather code (you can expand this)
                descriptions = {
                    0: "clear sky",
                    1: "mainly clear",
                    2: "partly cloudy",
                    3: "overcast",
                    45: "fog",
                    48: "depositing rime fog",
                    51: "light drizzle",
                    53: "moderate drizzle",
                    55: "dense drizzle",
                    56: "light freezing drizzle",
                    57: "dense freezing drizzle",
                    61: "slight rain",
                    63: "moderate rain",
                    65: "heavy rain",
                    66: "light freezing rain",
                    67: "heavy freezing rain",
                    71: "slight snow fall",
                    73: "moderate snow fall",
                    75: "heavy snow fall",
                    77: "snow grains",
                    80: "slight rain showers",
                    81: "moderate rain showers",
                    82: "violent rain showers",
                    85: "slight snow showers",
                    86: "heavy snow showers",
                    95: "thunderstorm",
                    96: "thunderstorm with slight hail",
                    99: "thunderstorm with heavy hail"
                }
                description = descriptions.get(weather_code, "unknown weather")
                print(f"🌤️ Weather information retrieved for {location}: {description}, {temp}°C, {windspeed} km/h" )
                
                return f"The weather in {location} is {description} with a temperature of {temp}°C and wind speed of {windspeed} km/h."
    except Exception as e:
        return f"Error fetching weather data: {str(e)}"

async def main():
    # Get Azure OpenAI configuration from environment variables
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    
    if not all([endpoint, api_key, deployment_name]):
        raise ValueError("Missing required Azure OpenAI configuration in .env file")
    
    print(f"🚀 Initializing Streaming Agent with Azure OpenAI...")
    print(f"   Endpoint: {endpoint}")
    print(f"   Deployment: {deployment_name}")
    
    # Create agent with Azure OpenAI Responses Client
    agent = AzureOpenAIResponsesClient(
        endpoint=endpoint,
        api_key=api_key,
        # api_version=api_version,  --> left out to use default
        deployment_name=deployment_name
    ).create_agent(
        name="WeatherBot",
        instructions="""You are a quirky weather expert assistant""",
        tools=[get_weather]  # Register the get_weather function as a tool
    )

    print("\n✅ WeatherBot initialized successfully!\n")

    thread = agent.get_new_thread()
    
    print("\n🎯 Chat Mode with Streaming Responses and Conversation Memory")
    print("Type your messages and see responses stream in real-time!")
    print("The agent will remember our entire conversation!")
    print("Type '/exit' to end the chat.\n")
    
    try:
        while True:
            try:
                # Get user input
                user_input = input("💬 You: ").strip()
                
                # Check for exit command
                if user_input.lower() == '/exit':
                    print("👋 Goodbye! Thanks for chatting!")
                    break
                
                if not user_input:
                    continue
                
                print("🤖 Agent: ", end="", flush=True)
                
                # Stream the response with conversation thread
                # The thread maintains conversation history automatically
                async for chunk in agent.run_stream(user_input, thread=thread):
                    if chunk.text:
                        print(chunk.text, end="", flush=True)
                
                print("\n")  # New line after streaming
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Thanks for chatting!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                continue
                
    finally:
        # Note: For Azure OpenAI Responses, threads may be persisted in the service
        # The framework handles cleanup automatically
        print("🧹 Cleaning up conversation thread...")
        print("✅ Session completed - conversation was managed by the service")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure you have:")
        print("1. Set up your .env file with Azure OpenAI credentials")
        print("2. Installed the required packages: pip install -r requirements.txt")
        print("3. Authenticated with Azure CLI: az login (if using Azure CLI credentials)")