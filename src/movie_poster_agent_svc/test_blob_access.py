#!/usr/bin/env python3
"""
Test script to verify blob access with managed identity.
"""
import asyncio
import os
import logging
from dotenv import load_dotenv
from main import PosterValidationAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_blob_access():
    """Test blob access with managed identity."""
    try:
        # Initialize the agent
        agent = PosterValidationAgent()
        
        # Test URL parsing
        test_blob_url = "https://nazrambihxklazmdpap4s.blob.core.windows.net/movieposters/525_3170_Romance_87490.png"
        
        print(f"Testing blob URL: {test_blob_url}")
        print(f"Is Azure blob URL: {agent._is_azure_blob_url(test_blob_url)}")
        
        # Test configuration
        print(f"Storage account URL: {agent.storage_account_url}")
        print(f"Blob service client configured: {agent.blob_service_client is not None}")
        
        if agent.blob_service_client:
            print("✅ Blob service client is properly configured with managed identity")
        else:
            print("❌ Blob service client is not configured")
            
        # You can test actual blob access here if you have a valid blob URL
        # result = await agent.encode_image_from_url(test_blob_url)
        # print(f"✅ Successfully encoded image: {len(result)} characters")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_blob_access())