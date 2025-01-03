
import requests
import logging
import time
import json
import random
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

#https://azrambi-openai-b76s6utvi44xo.openai.azure.com                /openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview 
#https://azure-rambi-apim-b76s6utvi44xo.azure-api.net/azure-openai-api/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview 



def describe_image2(poster_url):
    """Placeholder function to describe the image"""
    logger.info("Description of image at %s", poster_url)
    apim_base_url = "https://azure-rambi-apim-b76s6utvi44xo.azure-api.net"
    endpoint = "https://movie-poster-svc-b76s6utvi44xo.thankfuldesert-efbc16f5.francecentral.azurecontainerapps.io/describe/moana2?url=https://image.tmdb.org/t/p/w600_and_h900_bestv2/yh64qw9mgXBvlaWDi7Q9tpUBAvH.jpg"
    endpoint = "https://movie-poster-svc-b76s6utvi44xo.thankfuldesert-efbc16f5.francecentral.azurecontainerapps.io/describe/moana2?url=https://www.themoviedb.org/t/p/w600_and_h900_bestv2/dXNAPwY7VrqMAo51EKhhCJfaGb5.jpg" 
    endpoint = "https://azure-rambi-apim-b76s6utvi44xo.azure-api.net/movie_poster/describe/xx?url=https://www.themoviedb.org/t/p/w600_and_h900_bestv2/dXNAPwY7VrqMAo51EKhhCJfaGb5.jpg"
   
    random_number = random.randint(1, 100)
    logger.info("Generated random number: %d", random_number)
    query="the matrix"
    header = {
        "Ocp-Apim-Subscription-Key": "457a8296b79045c4a0adda71cfc9a0ec",
        "x-transaction-id": f"{query}-{random_number}"
    }
    logger.info("header: %s", header)
    logger.info("Calling APIM endpoint %s", apim_base_url)
    response = requests.get(f"{apim_base_url}/tmdb/3/search/movie?query={query}&include_adult=false&language=en-US&page=1", headers=header, timeout=100)
    if not response.status_code == 200:
        raise Exception("Failed to retrieve TMDB data: %s %s", response.status_code, response.text)
    
    tmdb_data = response.json()
    #print("tmdb_data %s", json.dumps(tmdb_data))
    title=tmdb_data['results'][0]["title"],
    url = f"https://image.tmdb.org/t/p/original/{tmdb_data['results'][0]["poster_path"]}"
    print("poster url %s", url)
    
    logger.info("Calling APIM endpoint %s", apim_base_url)
    response = requests.get(f"{apim_base_url}/movie_poster/describe/{title}?url={url}", headers=header, timeout=100)
    if not response.status_code == 200:
        raise Exception("Failed to retrieve movie poster data: %s %s", response.status_code, response.text)
    
    return response.content

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

