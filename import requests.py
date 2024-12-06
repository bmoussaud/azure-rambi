from azurerambi.movie_service import TMDBService
import requests
import os
from dotenv import load_dotenv
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

load_dotenv()

def search_movie(api_key, query):
    """ Search for a movie by title """
    url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={query}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None
    
    
def search_movie_apim(api_key, query):
    """ Search for a movie by title """
    url = f"https://azure-rambi-apim-b76s6utvi44xo.azure-api.net/tmdb/3/search/movie?query={query}"
    headers = {
        'Ocp-Apim-Subscription-Key': '457a8296b79045c4a0adda71cfc9a0ec'
    }
    response = requests.get(url, headers=headers)
  
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}, Reason: {response.reason}")
        return None
        
def search_movie2(api_key, query):
    """ Search for a movie by title """
    return TMDBService("https://azure-rambi-apim-b76s6utvi44xo.azure-api.net",api_key=api_key).get_movie_by_title(query)
    
if __name__ == "__main__":
    query = 'Inception'
    result = search_movie2("457a8296b79045c4a0adda71cfc9a0ec", query)
    if result:
        print(result)
    else:
        print("Failed to retrieve data")