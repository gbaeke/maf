"""Web search tool using Tavily API."""

import asyncio
import json
import logging
from typing import Annotated
from pydantic import Field
from tavily import AsyncTavilyClient

from agent_framework import ai_function

from config.config import TAVILY_API_KEY

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Custom formatter to show only filename, not full path
class ShortFileFormatter(logging.Formatter):
    def format(self, record):
        record.pathname = record.filename
        return super().format(record)

# Update root logger with custom formatter
root_logger = logging.getLogger()
for handler in root_logger.handlers:
    handler.setFormatter(ShortFileFormatter('[%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))

# Initialize Tavily client
if TAVILY_API_KEY:
    tavily_client = AsyncTavilyClient(TAVILY_API_KEY)
else:
    raise ValueError("Tavily API key is missing in environment variables.")


@ai_function(name="search_web", description="Search the web for information on multiple topics using Tavily")
async def search_web(
    queries: Annotated[list[str], Field(description="List of search queries to find information about")]
) -> str:
    """
    Search the web using Tavily API for multiple queries concurrently.
    Returns aggregated search results in JSON format organized by query.
    
    Args:
        queries: List of search query strings
        
    Returns:
        JSON string with aggregated results formatted as:
        {
            "query_1": [list of results],
            "query_2": [list of results],
            ...
        }
    """
    if not queries:
        return json.dumps({"error": "No queries provided"})
    
    logger.info(f"SEARCH - Performing web searches for {len(queries)} queries")
    
    async def _search_single_query(query: str) -> dict:
        """Perform a single web search using Tavily API."""
        if tavily_client is None:
            return {
                "query": query,
                "results": [],
                "error": "Tavily search is not available (API key not configured)"
            }
        
        try:
            logger.info(f'SEARCH - "{query}" - Searching')
            # Run the blocking Tavily search in a thread pool to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            response = await tavily_client.search(
                query=query,
                search_depth="advanced",
                max_results=5,
            )

            results = response.get("results", [])

            return {
                "query": query,
                "results": results,
                "error": None
            }
            
        except Exception as e:
            error_msg = f"Error searching for '{query}': {str(e)}"
            logger.error(f'SEARCH - "{query}" - {error_msg}')
            return {
                "query": query,
                "results": [],
                "error": error_msg
            }
    
    # Perform all searches concurrently
    tasks = [_search_single_query(query) for query in queries]
    search_results = await asyncio.gather(*tasks)
    
    # Aggregate results by query
    aggregated = {}
    errors = {}
    
    for result in search_results:
        query = result["query"]
        if result["error"]:
            errors[query] = result["error"]
            aggregated[query] = []
        else:
            aggregated[query] = result["results"]
    
    # Build final output
    output = {
        "results": aggregated
    }
    
    if errors:
        output["errors"] = errors
    
    # Save results to a file
    return json.dumps(output, indent=2)

