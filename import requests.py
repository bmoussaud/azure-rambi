from azurerambi.movie_service import TMDBService
import requests
import os
from dotenv import load_dotenv

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
    response = requests.get(url)
  
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}, Reason: {response.reason}")
        return None
        


def search_movie2(api_key, query):
    """ Search for a movie by title """
    return TMDBService().get_movie_by_title(query)
    
if __name__ == "__main__":
    api_key = os.getenv("TMDB_API_KEY")
    query = 'Inception'
    result = search_movie_apim(api_key, query)
    if result:
        print(result)
    else:
        print("Failed to retrieve data")