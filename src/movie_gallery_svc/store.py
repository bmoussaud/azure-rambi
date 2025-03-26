"""Movie store class to manage movie data."""
import logging
import json
from dapr.clients import DaprClient
from settings import Settings
from entities import Movie

logging.basicConfig(level=logging.INFO)

class MovieStore:
    """Class to manage the movie store."""
    def __init__(self, settings: Settings):
        self.settings = settings
        self.dapr_client = settings.dapr_client()
        self.state_store_name = settings.state_store_name
        self.state_store_query_index_name = settings.state_store_query_index_name
        self.binding_smtp = settings.binding_smtp

    def upsert(self, movie: Movie) -> Movie:
        """Add a movie to the store."""
        logging.info("Adding movie: %s", movie)
        self.dapr_client.save_state(
            store_name=self.state_store_name,
            key=movie['id'],
            value=json.dumps(movie),
            metadata={"content-type": "application/json"}
        )
        logging.info("Movie %s added to store", movie['id'])
        return self.try_find_by_id(movie['id'])
       
    def try_find_by_id(self, id : str) -> Movie:
        """Find a movie by its ID."""
        logging.info("Finding movie by ID: %s", id)
        try:
            response = self.dapr_client.get_state(
                store_name=self.state_store_name,
                key=id
            )
            if response.data:
                movie = Movie.from_bytes(response.data)
                logging.info("Movie found: %s", movie)
                return movie
            else:
                logging.info("Movie not found")
                return None
        except Exception as e:
            logging.error("Error finding movie by ID: %s", e)
            return None
   
    def find_all(self) -> list[Movie]:
        """Find all movies in the store."""
        logging.info("Finding all movies")
        try:
            response = self.dapr_client.query_state(
                store_name=self.state_store_query_index_name,
                query="SELECT * FROM movies"
            )
            movies = [Movie.from_bytes(item.data) for item in response.items]
            logging.info("Movies found: %s", movies)
            return movies
        except Exception as e:
            logging.error("Error finding all movies: %s", e)
            return []