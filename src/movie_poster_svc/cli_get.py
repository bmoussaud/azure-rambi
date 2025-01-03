
import requests
import logging
import time
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

#https://azrambi-openai-b76s6utvi44xo.openai.azure.com                /openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview 
#https://azure-rambi-apim-b76s6utvi44xo.azure-api.net/azure-openai-api/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview 



def describe_image2(poster_url):
    """Placeholder function to describe the image"""
    logger.info("Description of image at %s", poster_url)
    
    endpoint = "https://movie-poster-svc-b76s6utvi44xo.thankfuldesert-efbc16f5.francecentral.azurecontainerapps.io/movie_poster/describe/moana2?url=https://image.tmdb.org/t/p/w600_and_h900_bestv2/yh64qw9mgXBvlaWDi7Q9tpUBAvH.jpg"
    endpoint = "http://localhost:3100/describe/moana2?url=https://image.tmdb.org/t/p/w600_and_h900_bestv2/yh64qw9mgXBvlaWDi7Q9tpUBAvH.jpg"
    
    logger.info("Calling endpoint %s", endpoint)

    response = requests.get(endpoint, timeout=100)
    if response.status_code == 200:
        return response.content
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

