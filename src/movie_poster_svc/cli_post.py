import json

import requests
import os

import logging
import time
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

#https://azrambi-openai-b76s6utvi44xo.openai.azure.com                /openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview 
#https://azure-rambi-apim-b76s6utvi44xo.azure-api.net/azure-openai-api/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview 



def generate_image(poster: dict):
    """Placeholder function to describe the image"""
    logger.info("generate_image of image at %s", poster['title'])
    endpoint = "http://movie-poster-svc-b76s6utvi44xo.graywater-74a15be5.francecentral.azurecontainerapps.io/movie_poster/generate"
    #endpoint = "http://localhost:8000/movie_poster/generate"

    logger.info("Calling endpoint %s", endpoint)
    logger.info(json.dumps(poster))

    response = requests.post(endpoint, json=poster, timeout=100)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error("Failed to retrieve data: %s %s", response.status_code, response.text)
        return None

if __name__ == "__main__":
    all =[]
    for attempt in range(1):
        logger.info("Attempt %d", attempt + 1)
        start_time = time.time()
        poster = {
            'title': 'The Blues Brothers',
            'description': 'The poster features two characters dressed in black suits, white shirts, black ties, and black hats, standing side by side against a police lineup backdrop with height measurements. Each character is holding a sign resembling a mugshot placard. One placard reads "THE BLUES" with details: 01A4392, BLUES, ELWOOD, 6\'1", 220 lbs. The other placard reads "BROTHERS" with details: 01A4391, BLUES, JAKE, 5\'8", 225 lbs. The character with the "BROTHERS" placard has the name "JAKE" tattooed across the fingers of one hand. The overall aesthetic suggests a playful yet mischievous tone, hinting at a comedic narrative.',
        }
        result = generate_image(poster)
        all.append(time.time() - start_time)
        logger.info("Time taken: %s seconds", all[-1])

    mean_time = sum(all) / len(all)
    logger.info("Mean time taken: %s seconds", mean_time)

    if result:
        logger.info(result)
    else:
        logger.error("Failed to retrieve data")

