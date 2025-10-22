"""Movie store class to manage movie data."""
import logging
import json
import traceback
from entities import GeneratedMovie, Movie
from dapr.clients import DaprClient

logging.basicConfig(level=logging.INFO)


class MovieStore:
  
    """Class to manage the movie store."""
    def __init__(self, dapr_client : DaprClient):
        self.dapr_client = dapr_client
        self.state_store_name = 'movie-gallery-svc-statetore'
        
    def upsert(self, movie: GeneratedMovie) -> GeneratedMovie:
        """Add a movie to the store."""
        logging.info("Adding movie: %s", movie)
        logging.info("JSON %s", movie.to_json())
        movie_id = movie.id
        logging.info("Saving movie to store %s using this key %s", self.state_store_name, movie_id)
        self.dapr_client.save_state(
            store_name=self.state_store_name,
            key=movie_id,
            value=movie.to_json()
        )
        logging.info("Movie %s added to store", movie_id)
        return self.try_find_by_id(movie_id)
       
    def try_find_by_id(self, movie_id : str) -> Movie:
        """Find a movie by its ID."""
        logging.info("Finding movie by ID: %s", movie_id)
        try:
            response = self.dapr_client.get_state(
                store_name=self.state_store_name,
                key=movie_id
            )
            if response.data:
                logging.info("Movie found in store data: %s", response.data)
                movie = GeneratedMovie.from_json(response.data)
                logging.info("Movie found: %s", movie)
                return movie
            else:
                logging.info("Movie not found")
                return None
        except Exception as e:
            logging.error("Error finding movie by ID: %s", e)
            raise e
   
    def find_all(self) -> list[Movie]:
        """Find all movies in the store."""
        logging.info("Finding all movies")
        try:
            query_all_with_limit = '''
            {
                "page": {
                    "limit": 100
                }
            }
            '''
            query_all = "{}"
            query = query_all
            states_metadata = {"contentType": "application/json"}
            logging.info("Query: %s", query)
            logging.info("States metadata: %s", states_metadata)
            logging.info("Store name: %s", self.state_store_name)
            logging.info("Querying state store")
            response = self.dapr_client.query_state(
                    store_name=self.state_store_name,
                    query=query,
                    states_metadata=states_metadata
                )
            movies = [GeneratedMovie.from_json(item.value) for item in response.results]
            logging.info("GeneratedMovies found: %d", len(movies))
            return movies
        except Exception as e:
            logging.error("Error finding all movies: %s", e)
            logging.error("Call stack: %s", traceback.format_exc())
            logging.error("Returning empty list")
            return []
        
    def delete(self, movie_id: str) -> bool:
        """Delete a movie from the store by its ID."""
        logging.info("Deleting movie by ID: %s", movie_id)
        try:
            self.dapr_client.delete_state(
                store_name=self.state_store_name,
                key=movie_id
            )
            logging.info("Movie %s deleted from store", movie_id)
            return True
        except Exception as e:
            logging.error("Error deleting movie by ID: %s", e)
            return False