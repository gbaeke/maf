"""Gamma API client for presentation generation."""

import asyncio
import json
import logging
import time
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class GammaAPIClient:
    """
    Client for interacting with the Gamma API.
    
    This class provides methods to generate presentations using the Gamma API.
    It handles request creation, polling for completion, and PDF downloads.
    """
    
    def __init__(
        self,
        api_key: str,
        api_base_url: str,
        text_mode: str = "condense",
        format: str = "presentation",
        theme_name: str = "Gamma",
        num_cards_offset: int = 1,
        card_split: str = "auto",
        export_as: str = "pdf",
        text_amount: str = "brief",
        text_tone: str = "professional, engaging, informative",
        text_language: str = "en",
        text_audience: str = "general",
        image_source: str = "aiGenerated",
        image_style: str = "photorealistic",
        card_dimensions: str = "16x9",
        poll_interval: int = 5,
        max_wait: int = 300,
        request_timeout: int = 30,
        extra_params: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the Gamma API client with all configurable parameters.
        
        Args:
            api_key: Your Gamma API key
            api_base_url: Base URL for the Gamma API
            text_mode: "generate" or "condense"
            format: Presentation format (default: "presentation")
            theme_name: Presentation theme name
            num_cards_offset: Additional cards beyond number_of_slides (e.g., 1 for title slide)
            card_split: How to split content across cards (default: "auto")
            export_as: Export format (default: "pdf")
            text_amount: Text amount ("brief", "medium", "detailed")
            text_tone: Tone for text generation
            text_language: Language code (default: "en")
            text_audience: Target audience
            image_source: Image source ("aiGenerated", "stock", "custom")
            image_style: Image style
            card_dimensions: Card dimensions ("16x9", "4x3")
            poll_interval: Seconds between status polls
            max_wait: Maximum seconds to wait for completion
            request_timeout: Request timeout in seconds
            extra_params: Additional parameters to pass to API
        """
        if not api_key:
            raise ValueError("API key is required")
        if not api_base_url:
            raise ValueError("API base URL is required")
        
        self.api_key = api_key
        self.api_base_url = api_base_url
        self.text_mode = text_mode
        self.format = format
        self.theme_name = theme_name
        self.num_cards_offset = num_cards_offset
        self.card_split = card_split
        self.export_as = export_as
        self.text_amount = text_amount
        self.text_tone = text_tone
        self.text_language = text_language
        self.text_audience = text_audience
        self.image_source = image_source
        self.image_style = image_style
        self.card_dimensions = card_dimensions
        self.poll_interval = poll_interval
        self.max_wait = max_wait
        self.request_timeout = request_timeout
        self.extra_params = extra_params or {}
    
    def _get_headers(self, include_accept: bool = False) -> Dict[str, str]:
        """
        Get HTTP headers for API requests.
        
        Args:
            include_accept: Whether to include Accept header
            
        Returns:
            Dictionary of headers
        """
        headers = {
            "X-API-KEY": self.api_key,
        }
        
        if include_accept:
            headers["accept"] = "application/json"
        else:
            headers["Content-Type"] = "application/json"
        
        return headers
    
    async def create_presentation(
        self,
        input_text: str,
        number_of_slides: int,
        audience: Optional[str] = None,
        title: str = "Presentation",
    ) -> Dict[str, Any]:
        """
        Create a presentation using the Gamma API.
        
        Args:
            input_text: The content to convert to a presentation
            number_of_slides: Number of slides in the presentation
            audience: Target audience for the presentation
            title: Title for logging purposes
            
        Returns:
            Dictionary containing generation_id, pdf_url, and completion data
            
        Raises:
            ValueError: If API request fails or returns invalid data
            TimeoutError: If presentation generation times out
        """
        logger.info(f'GAMMA - "{title}" - Slides: {number_of_slides}, Audience: {audience or "general"}')
        
        # Create payload with current settings
        audience_to_use = audience or self.text_audience
        payload = {
            "inputText": input_text,
            "textMode": self.text_mode,
            "format": self.format,
            "themeName": self.theme_name,
            "numCards": number_of_slides + self.num_cards_offset,
            "cardSplit": self.card_split,
            "exportAs": self.export_as,
            "textOptions": {
                "amount": self.text_amount,
                "tone": self.text_tone,
                "language": self.text_language,
                "audience": audience_to_use,
            },
            "imageOptions": {
                "source": self.image_source,
                "style": self.image_style,
            },
            "cardOptions": {
                "dimensions": self.card_dimensions,
            },
        }
        
        # Add any extra parameters
        payload.update(self.extra_params)
        
        # POST request to create generation
        generation_id = await self._post_generation(payload, title)
        
        # Poll for completion
        completed_data = await self._poll_for_completion(generation_id, title)
        
        # Extract and download PDF
        pdf_url = completed_data.get("exportUrl")
        if not pdf_url:
            raise ValueError(f"No PDF URL in response: {json.dumps(completed_data, indent=2)}")
        
        pdf_path = self._download_pdf(
            pdf_url,
            output_path=f"{title.replace(' ', '_')}.pdf"
        )
        
        return {
            "generation_id": generation_id,
            "pdf_url": pdf_url,
            "pdf_path": pdf_path,
            "completed_data": completed_data,
        }
    
    async def _post_generation(self, payload: Dict[str, Any], title: str) -> str:
        """
        POST request to create a new generation.
        
        Args:
            payload: Request payload
            title: Title for logging
            
        Returns:
            Generation ID
            
        Raises:
            ValueError: If request fails
        """
        headers = self._get_headers(include_accept=False)
        headers["Content-Type"] = "application/json"
        
        try:
            response = requests.post(
                f"{self.api_base_url}/generations",
                headers=headers,
                json=payload,
                timeout=self.request_timeout,
            )
            
            if response.status_code not in [200, 201]:
                error_msg = f"Gamma API Error: {response.status_code} - {response.text}"
                logger.error(f'GAMMA - "{title}" - POST /generations {response.status_code}')
                raise ValueError(error_msg)
            
            data = response.json()
            generation_id = data.get("id") or data.get("generationId")
            
            if not generation_id:
                raise ValueError(f"No generation ID in response: {json.dumps(data, indent=2)}")
            
            logger.info(f'GAMMA - "{title}" - POST /generations {response.status_code} - Generation ID: {generation_id}')
            return generation_id
            
        except requests.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(f'GAMMA - "{title}" - {error_msg}')
            raise ValueError(error_msg) from e
    
    async def _poll_for_completion(
        self,
        generation_id: str,
        title: str = "Presentation",
    ) -> Dict[str, Any]:
        """
        Poll the API until the presentation is completed.
        
        Args:
            generation_id: ID of the generation to poll
            title: Title for logging
            
        Returns:
            Completed generation data
            
        Raises:
            TimeoutError: If generation doesn't complete within max_wait
        """
        headers = self._get_headers(include_accept=True)
        
        logger.info(
            f'GAMMA - GET /generations/{generation_id} - Polling started '
            f'(max wait: {self.max_wait}s)'
        )
        start_time = time.time()
        
        while time.time() - start_time < self.max_wait:
            try:
                response = requests.get(
                    f"{self.api_base_url}/generations/{generation_id}",
                    headers=headers,
                    timeout=self.request_timeout,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status")
                    
                    if status == "completed":
                        logger.info(f'GAMMA - GET /generations/{generation_id} - Status: completed')
                        return data
                    
                    elapsed = int(time.time() - start_time)
                    logger.info(
                        f'GAMMA - GET /generations/{generation_id} - Status: {status} ({elapsed}s)'
                    )
                
                await asyncio.sleep(self.poll_interval)
                
            except requests.RequestException as e:
                logger.warning(f'GAMMA - Polling request failed: {str(e)}, retrying...')
                await asyncio.sleep(self.poll_interval)
        
        raise TimeoutError(
            f"Presentation generation timed out after {self.max_wait} seconds"
        )
    
    def _download_pdf(self, pdf_url: str, output_path: str = "presentation.pdf") -> str:
        """
        Download the PDF from the provided URL.
        
        Args:
            pdf_url: URL of the PDF file
            output_path: Path where to save the PDF
            
        Returns:
            Path to the saved PDF file
            
        Raises:
            RuntimeError: If download fails
        """
        logger.info(f'GAMMA - Downloading PDF to: {output_path}')
        
        try:
            response = requests.get(pdf_url, timeout=self.request_timeout)
            
            if response.status_code != 200:
                raise RuntimeError(
                    f"Failed to download PDF (status {response.status_code})"
                )
            
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            logger.info(f'GAMMA - PDF saved successfully to: {output_path}')
            return output_path
            
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to download PDF: {str(e)}") from e
