import json
from azurerambi.movie_service import GenAiMovieService
import requests
import os
from dotenv import load_dotenv
import logging
import time
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

#https://azrambi-openai-b76s6utvi44xo.openai.azure.com                /openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview 
#https://azure-rambi-apim-b76s6utvi44xo.azure-api.net/azure-openai-api/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview 


load_dotenv()
os.environ["AZURE_OPENAI_ENDPOINT"]="https://azrambi-openai-b76s6utvi44xo.openai.azure.com"
os.environ["AZURE_OPENAI_SUBSCRIPTION_KEY"]="7e33943656894e78bda27a309f907998"

os.environ["AZURE_OPENAI_ENDPOINT"]="https://azure-rambi-apim-b76s6utvi44xo.azure-api.net/azure-openai-api"
os.environ["AZURE_OPENAI_ENDPOINT"]="https://azure-rambi-apim-b76s6utvi44xo.azure-api.net/azure-rambi"
def describe_image(url):
    """Placeholder function to describe the image"""
    logger.info("Description of image at %s", url)
    svc = GenAiMovieService()
    info = svc.describe_poster(url)
    return info

def describe_image2(poster_url):
    """Placeholder function to describe the image"""
    logger.info("Description of image at %s", poster_url)
    headers = {
        "Content-Type": "application/json",
        "api-key": os.getenv("AZURE_OPENAI_SUBSCRIPTION_KEY")
    }
    #endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") + "/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview"
    endpoint = "https://azrambi-openai-b76s6utvi44xo.openai.azure.com/openai/deployments/gpt-4/chat/completions?api-version=2024-08-01-preview"
    endpoint = "https://azrambi-openai-b76s6utvi44xo.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-02-01"
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") + "/openai/deployments/gpt-4o/chat/completions?api-version=2024-02-01"
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") + "/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview"
    messages=[
                {"role": "system", "content": "You are a helpful assistant to describe movie posters."},
                {"role": "user", "content": [
                    {
                        "type": "text",
                        "text": "Describe this movie poster:"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                                "url": poster_url
                        }
                    }
                ]}
            ]
    data = {
        "messages": messages
    }
    logger.info("Calling endpoint %s with data:", endpoint)
    #logger.info(json.dumps(data, indent=2))
    response = requests.post(endpoint, headers=headers, json=data, timeout=100)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        logger.error("Failed to retrieve data: %s %s", response.status_code, response.text)
        return None

if __name__ == "__main__":
    all =[]
    for attempt in range(1):
        logger.info("Attempt %d", attempt + 1)
        start_time = time.time()
        result = describe_image2("https://image.tmdb.org/t/p/w600_and_h900_bestv2/yh64qw9mgXBvlaWDi7Q9tpUBAvH.jpg")
        all.append(time.time() - start_time)
        logger.info("Time taken: %s seconds", all[-1])

    mean_time = sum(all) / len(all)
    logger.info("Mean time taken: %s seconds", mean_time)

    if result:
        logger.info(result)
    else:
        logger.error("Failed to retrieve data")

