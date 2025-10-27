from io import BytesIO
from agent_framework import AgentRunResponse, ChatAgent, ChatMessage, ai_function
from agent_framework.openai import OpenAIResponsesClient

import asyncio
import os
import httpx
import logging
import base64
from urllib.parse import urlparse
from random import randrange
from typing import TYPE_CHECKING, Annotated, Any
from azure.storage.blob import BlobServiceClient
from PIL import Image
from azure.identity import ManagedIdentityCredential, DefaultAzureCredential

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@ai_function
def get_image_content(url: Annotated[str, "fetch the content from url pointing to an image stored in Azure Blob Storage, base64 encoded content"]) -> str:
    logger.info(f"AI_FUNCTION: Getting image content from URL: {url}")
    client_id = os.getenv("AZURE_CLIENT_ID", None)
    return ImageLoader(client_id).encode_image_from_url(url)


class ImageLoader:
    def __init__(self, client_id: str = None):
        # Use managed identity for blob storage access
        if client_id:
            logger.info(f"Using managed identity {client_id} for blob storage access")
            self._credential = ManagedIdentityCredential(client_id=client_id)
        else:
            logger.info("Using default Azure credential for blob storage access")
            self._credential = DefaultAzureCredential()
        logger.info(f"Credential initialized: {self._credential}")
        

    def _blob_service_client(self, storage_account_url: str) -> str:
        return BlobServiceClient(
            account_url=storage_account_url,
            credential=self._credential
        )

    def encode_image_from_url(self, image_url: str) -> str:
        logger.info(f"Encoding image from URL: {image_url}")
        """Encode image from URL to base64, using managed identity for Azure blob storage URLs."""
        try:
            # Check if this is an Azure blob storage URL
            if self._is_azure_blob_url(image_url):
                logger.info("Detected Azure blob storage URL, using authenticated access")
                return self._encode_image_from_blob_url(image_url)
            else:
                # Regular HTTP URL - use direct access
                logger.info("Using direct HTTP access for non-blob URL")
                with httpx.Client() as client:
                    response = client.get(image_url)
                    response.raise_for_status()
                    
                    logger.info(f"Image fetched successfully: {len(response.content)} bytes")
                    image = Image.open(BytesIO(response.content))
                    
                    # Convert to base64
                    logger.info("Encoding image to base64")
                    return base64.b64encode(response.content).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image from URL {image_url}: {str(e)}")
            raise RuntimeError(f"Failed to process image from URL: {str(e)}") from e
    
    def _is_azure_blob_url(self, url: str) -> bool:
        """Check if URL is an Azure blob storage URL."""
        try:
            parsed = urlparse(url)
            logger.info(f"Parsed URL netloc: {parsed.netloc}")
            return 'blob.core.windows.net' in parsed.netloc
        except Exception:
            return False
    
    def _encode_image_from_blob_url(self, blob_url: str) -> str:
        """Encode image from Azure blob storage URL using managed identity."""
        try:
            # Parse the blob URL to extract container and blob name
            parsed = urlparse(blob_url)
            path_parts = parsed.path.lstrip('/').split('/')
            logger.info(f"Parsed blob URL path parts: {path_parts}")

            if len(path_parts) < 2:
                raise RuntimeError("Invalid blob URL format: {blob_url}")
            
            container_name = path_parts[0]
            blob_name = '/'.join(path_parts[1:])
            
            logger.info(f"Accessing blob: container={container_name}, blob={blob_name}")
            
            # Get blob client and download content
            blob_client = self._blob_service_client(parsed.netloc).get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            # Download blob content
            with blob_client:
                blob_data = blob_client.download_blob()
                content = blob_data.readall()
            
            logger.info(f"Blob downloaded successfully: {len(content)} bytes")
            
            # Validate it's an image
            image = Image.open(BytesIO(content))
            
            # Convert to base64
            logger.info("Encoding blob image to base64")
            return base64.b64encode(content).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error accessing blob {blob_url}: {str(e)}")
            raise RuntimeError(
                f"Failed to access blob with managed identity: {str(e)}" 
            ) from e
    