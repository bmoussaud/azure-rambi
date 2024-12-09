from azurerambi.movie_service import GenAiMovieService
import requests
import os
from dotenv import load_dotenv
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

#https://azrambi-openai-b76s6utvi44xo.openai.azure.com                /openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview 
#https://azure-rambi-apim-b76s6utvi44xo.azure-api.net/azure-openai-api/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview 


load_dotenv()
os.environ["AZURE_OPENAI_ENDPOINT"]="https://azure-rambi-apim-b76s6utvi44xo.azure-api.net/azure-openai-api"
#os.environ["AZURE_OPENAI_SUBSCRIPTION_KEY"]="457a8296b79045c4a0adda71cfc9a0ec"
def describe_image(url):
    """Placeholder function to describe the image"""
    logger.info (f"Description of image at {url}")
    svc = GenAiMovieService()
    info = svc.describe_poster(url)
    return info

def describe_image2(poster_url):
    """Placeholder function to describe the image"""
    logger.info (f"Description of image at {poster_url}")
    headers = {
        "Content-Type": "application/json",
        "api-key": os.getenv("AZURE_OPENAI_SUBSCRIPTION_KEY")
    }
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
    logger.info(f"Calling endpoint {endpoint} with data {data}")
    response = requests.post(endpoint, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        logger.error(f"Failed to retrieve data: {response.status_code} {response.text}")
        return None

if __name__ == "__main__":
    result = describe_image2("https://image.tmdb.org/t/p/w600_and_h900_bestv2/yh64qw9mgXBvlaWDi7Q9tpUBAvH.jpg")
    if result:
        logger.info(result)
    else:
        logger.error("Failed to retrieve data")

