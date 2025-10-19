#!/usr/bin/env python3
"""
Simple script to create a presentation using the Gamma API and export it to PDF.
"""

import sys
import json
import time
import requests
from pathlib import Path

from config.config import API_KEY, API_BASE_URL


def create_presentation(input_text: str, theme: str = "Oasis", num_cards: int = 5) -> dict:
    """
    Create a presentation using the Gamma API.

    Args:
        input_text: The topic or content for the presentation
        theme: Theme name (default: Oasis)
        num_cards: Number of cards to generate (default: 5)

    Returns:
        Response data from the API
    """
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": API_KEY,
    }

    payload = {
        "inputText": input_text,
        "textMode": "generate",
        "format": "presentation",
        "themeName": theme,
        "numCards": num_cards,
        "cardSplit": "auto",
        "exportAs": "pdf",
        "textOptions": {
            "amount": "medium",
            "tone": "professional, engaging",
            "language": "en",
        },
        "imageOptions": {
            "source": "aiGenerated",
            "style": "photorealistic",
        },
        "cardOptions": {
            "dimensions": "16x9",
        },
    }

    print(f"Creating presentation: '{input_text}'...")
    print(f"Theme: {theme}, Cards: {num_cards}")

    response = requests.post(
        f"{API_BASE_URL}/generations",
        headers=headers,
        json=payload,
    )

    if response.status_code not in [200, 201]:
        print(f"Error: API returned status {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)

    return response.json()


def poll_for_completion(generation_id: str, max_wait: int = 300) -> dict:
    """
    Poll the API to check if the presentation is ready.

    Args:
        generation_id: The ID of the generation
        max_wait: Maximum time to wait in seconds (default: 300)

    Returns:
        The completed generation data
    """
    headers = {
        "X-API-KEY": API_KEY,
        "accept": "application/json",
    }

    print(f"\nPolling for completion (max wait: {max_wait}s)...")
    start_time = time.time()

    while time.time() - start_time < max_wait:
        response = requests.get(
            f"{API_BASE_URL}/generations/{generation_id}",
            headers=headers,
        )

        if response.status_code != 200:
            print(f"Error: API returned status {response.status_code}")
            print(f"Response: {response.text}")
            sys.exit(1)

        data = response.json()
        status = data.get("status")

        if status == "completed":
            print("✓ Presentation completed!")
            print(f"Full response: {json.dumps(data, indent=2)}")
            return data

        print(f"Status: {status}... ({int(time.time() - start_time)}s)")
        time.sleep(5)

    print(f"Error: Presentation generation timed out after {max_wait} seconds")
    sys.exit(1)


def download_pdf(pdf_url: str, output_path: str = "presentation.pdf") -> None:
    """
    Download the PDF from the provided URL.

    Args:
        pdf_url: URL of the PDF file
        output_path: Path where to save the PDF
    """
    print(f"\nDownloading PDF to: {output_path}...")

    response = requests.get(pdf_url)

    if response.status_code != 200:
        print(f"Error: Failed to download PDF (status {response.status_code})")
        sys.exit(1)

    with open(output_path, "wb") as f:
        f.write(response.content)

    print(f"✓ PDF saved successfully!")


def main():
    """Main function to orchestrate the presentation creation."""
    # Example topic for the presentation
    topic = "The Future of Artificial Intelligence"

    # Create the presentation
    creation_response = create_presentation(
        input_text=topic,
        theme="Oasis",
        num_cards=5,
    )

    generation_id = creation_response.get("id") or creation_response.get("generationId")
    if not generation_id:
        print("Error: No generation ID returned from API")
        print(f"Response: {json.dumps(creation_response, indent=2)}")
        sys.exit(1)

    print(f"Generation ID: {generation_id}")

    # Poll for completion
    completed_data = poll_for_completion(generation_id)

    # Extract PDF URL and download
    # The PDF URL is in exportUrl (singular string)
    pdf_url = completed_data.get("exportUrl")
    
    if pdf_url:
        print(f"\nPDF URL found: {pdf_url}")
        download_pdf(pdf_url, output_path="presentation.pdf")
        print(f"\n✓ All done! Your presentation is ready: presentation.pdf")
    else:
        print("Warning: No PDF URL found in response")
        print(f"Full response: {json.dumps(completed_data, indent=2)}")


if __name__ == "__main__":
    main()
