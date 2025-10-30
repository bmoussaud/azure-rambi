"""Movie store class to manage movie data."""
import logging
import json
import traceback
from entities import PosterValidationResponse
from dapr.clients import DaprClient

logging.basicConfig(level=logging.INFO)


class ValidationStore:
  
    """Class to manage the movie store."""
    def __init__(self, dapr_client : DaprClient):
        self.dapr_client = dapr_client
        self.state_store_name = 'movie-poster-agent-svc-statetore'
        
    def upsert(self, validation: PosterValidationResponse) -> PosterValidationResponse:
        """Add a PosterValidationResponse to the store."""
        logging.info("Adding PosterValidationResponse: %s", validation)
        logging.info("JSON %s", validation.to_json())
        movie_id = validation.id
        logging.info("Saving movie to store %s using this key %s", self.state_store_name, movie_id)
        self.dapr_client.save_state(
            store_name=self.state_store_name,
            key=movie_id,
            value=validation.to_json()
        )
        logging.info("Validation %s added to store", movie_id)
        return self.try_find_by_id(movie_id)
       
    def try_find_by_id(self, movie_id : str) -> PosterValidationResponse:
        """Find a movie by its ID."""
        logging.info("Finding movie by ID: %s", movie_id)
        try:
            response = self.dapr_client.get_state(
                store_name=self.state_store_name,
                key=movie_id
            )
            if response.data:
                logging.info("Validation found in store data: %s", response.data)
                validation = PosterValidationResponse.from_json(response.data)
                logging.info("Validation found: %s", validation)
                return validation
            else:
                logging.info("Validation not found")
                return None
        except Exception as e:
            logging.error("Error finding Validation by ID: %s", e)
            raise e
   
    def find_all(self) -> list[PosterValidationResponse]:
        """Find all PosterValidationResponse in the store."""
        logging.info("Finding all PosterValidationResponse")
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
            movies = [PosterValidationResponse.from_json(item.value) for item in response.results]
            logging.info("PosterValidationResponse found: %d", len(movies))
            return movies
        except Exception as e:
            logging.error("Error finding all movies: %s", e)
            logging.error("Call stack: %s", traceback.format_exc())
            logging.error("Returning empty list")
            return []
        
    def delete(self, movie_id: str) -> bool:
        """Delete a PosterValidationResponse from the store by its ID."""
        logging.info("Deleting PosterValidationResponse by ID: %s", movie_id)
        try:
            self.dapr_client.delete_state(
                store_name=self.state_store_name,
                key=movie_id
            )
            logging.info("PosterValidationResponse %s deleted from store", movie_id)
            return True
        except Exception as e:
            logging.error("Error deleting PosterValidationResponse by ID: %s", e)
            return False