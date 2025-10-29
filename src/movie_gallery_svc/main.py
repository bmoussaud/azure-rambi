import json
import logging
import uvicorn
import traceback
import base64

from entities import GeneratedMovie
from store import MovieStore
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from fastapi import FastAPI, Response, status, Request
from fastapi.responses import HTMLResponse
from dapr.clients import DaprClient
from dapr.ext.fastapi import DaprApp
from cloudevents.http import from_http



logging.basicConfig(level=logging.INFO)

app = FastAPI()
dapr_app = DaprApp(app)
dapr_client = DaprClient()
store=MovieStore(dapr_client)

FastAPIInstrumentor.instrument_app(app, excluded_urls="liveness,readiness")

# Define the storage queue binding name
STORAGE_QUEUE_BINDING = "movieposters-events-queue"

@app.get('/', response_class = HTMLResponse)
def root():
    """
    Root endpoint to check if the service is running.
    """
    logging.info("Movie Gallery API is running")
    return """
    <html>
        <head>
            <title>Movie Gallery API</title>
        </head>
        <body>
            <pre>Movie Gallery API Ready !</pre>
        </body>
    </html>
    """

# Dapr subscription in /dapr/subscribe sets up this route
@app.route('/' + STORAGE_QUEUE_BINDING, methods=['POST'])
async def movieposters_events_handler(request: Request):
    """
    Endpoint to receive messages from the Azure Storage Queue.
    
    Handles CloudEvents encoded as base64 from Azure Event Grid to Storage Queue.
    Extracts blob information and updates movie records with poster URLs.
    """
    try:
        logging.info("Received message from Azure Storage Queue")
        # Get request body as bytes
        body = await request.body()
        
        # For debugging - print the raw headers and a sample of the body
        logging.debug("Headers: %s", request.headers)
        logging.debug("Body sample (first 100 chars): %s", body[:100] if body else "Empty body")
        
        try:
            # decode the body as a CloudEvent
            decoded_body = base64.b64decode(body)
            payload = json.loads(decoded_body)
            logging.info("Successfully decoded base64 body: %s", str(payload))
            # Log the JSON dump of the payload for debugging purposes
            logging.debug("JSON dump of payload: %s", json.dumps(payload, indent=2))
            # Extract the data from the decoded body
            payload_data = payload.get('data', {})
            logging.info("Extracted data from decoded body: %s", str(payload_data))
            event = {
                'type': payload.get('type', 'unknown'),
                'subject': payload.get('subject', ''),
                'time': payload.get('time', ''),
                'id': payload.get('id', ''),
                'source': payload.get('source', ''),
                'data': payload_data
            }
            logging.info("Created event from payload: type=%s, subject=%s", event['type'], event['subject'])
        except Exception as parse_error:
            logging.error("Failed to parse message: %s", parse_error)
            raise ValueError("Unable to parse message in any format") from parse_error
        
        # Process the event data - for Azure Storage blob events
        if 'subject' in event and event['subject'] and 'type' in event and 'Microsoft.Storage.BlobCreated' in event['type']:
            # Extract information from the blob path in subject
            # Format is typically: /blobServices/default/containers/{containerName}/blobs/{blobName}
            subject = event['subject']
            logging.info("Processing blob created event: %s", subject)
            
            # Extract the blob information
            parts = subject.split('/')
            if len(parts) >= 6 and parts[3] == 'containers' and parts[5] == 'blobs':
                container_name = parts[4]
                blob_name = '/'.join(parts[6:])  # Join in case the blob name contains slashes
                
                # Extract movie_id from blob name - assuming format like "525_346698_Romance_10630.png"
                # where 525_346698_Romance_10630 is the movie_id
                try:
                    movie_id = blob_name.split('.')[0]
                    logging.info("Extracted movie ID %s from blob %s", movie_id, blob_name)
                    
                    # Construct the poster URL
                    blob_url = None
                    if 'data' in event and isinstance(event['data'], dict):
                        # Try to get URL directly from event data
                        blob_url = event['data'].get('url')
                    
                    if not blob_url and 'data' in event and isinstance(event['data'], dict) and 'url' in event['data']:
                        blob_url = event['data']['url']
                    
                    # If URL not in event data, construct it (fallback)
                    if not blob_url:
                        # Get storage account from the source field which contains the resource ID
                        source = event.get('source', '')
                        account_name = None
                        if 'storageAccounts/' in source:
                            account_name = source.split('storageAccounts/')[1].split('/')[0]
                        
                        if account_name:
                            blob_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}"
                        else:
                            logging.warning("Could not determine storage account name from event source: %s", source)
                            # Use a placeholder or skip processing
                            return Response(
                                content=json.dumps({"success": False, "error": "Could not determine storage account name"}),
                                media_type="application/json",
                                status_code=status.HTTP_400_BAD_REQUEST
                            )
                    
                    logging.info("Blob URL: %s", blob_url)
                    
                    # Get the movie and update it with the poster URL
                    movie = store.try_find_by_id(movie_id)
                    if movie:
                        movie.internal_poster_url = blob_url
                        movie.poster_url = f"/poster/{movie_id}.png"
                        store.upsert(movie)
                        logging.info("Updated movie %s with poster URL %s", movie_id, blob_url)
                        logging.info("Publishing movie update event for movie ID %s", movie_id)
                        # Publish an event to notify other services of the update
                        dapr_client.publish_event(pubsub_name="moviepubsub", topic_name="movie-updates", data=json.dumps(movie.to_json()))
                    else:
                        logging.warning("Movie %s not found in data store", movie_id)
                except Exception as extract_error:
                    logging.error("Error extracting data from blob name: %s", extract_error)
            else:
                logging.warning("Invalid blob subject format: %s", subject)
        else:
            logging.warning("Event is not a blob created event or missing required fields: %s", event)
        
        # Return successful response
        return Response(
            content=json.dumps({"success": True}),
            media_type="application/json",
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        logging.error("Error processing movie poster event: %s", str(e))
        logging.error("Call stack: %s", traceback.format_exc())
        # We still return success to prevent the queue message from being retried endlessly
        return Response(
            content=json.dumps({"success": False, "error": str(e)}),
            media_type="application/json",
            status_code=status.HTTP_200_OK  # Use 200 to acknowledge receipt even on error
        )

@app.post("/movies", status_code = status.HTTP_201_CREATED)
def add_movie(movie: GeneratedMovie) -> GeneratedMovie:
    """Endpoint to add a new movie."""
    try:
        logging.info("Adding new movie %s", movie)
        inserted_generated_movie=store.upsert(movie)
        return inserted_generated_movie
    except Exception as e:
        logging.error('Add_Movie Error: %s', e)
        logging.error('Call stack: %s', traceback.format_exc())
        return Response(content = json.dumps({'method':'add_movie','error':e}), media_type = "application/json")

@app.get("/movies/{movie_id}", response_model=GeneratedMovie)
def get_movie(movie_id: str) -> GeneratedMovie:
    """Endpoint to get a movie by ID."""
    logging.info("Getting movie with ID: %s", movie_id)
    try:
        movie = store.try_find_by_id(movie_id)
        if movie:
            return movie
        else:
            return Response(content=json.dumps({}), media_type="application/json", status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logging.error('Get_Movie Error: %s', e)
        logging.error('Call stack: %s', traceback.format_exc())
        return Response(content=json.dumps({'method':'get_movie','error':e}), media_type="application/json")
    

@app.get("/movies", response_model=list[GeneratedMovie])
def list_movies() -> list[GeneratedMovie]:
    """Endpoint to list all movies."""
    logging.info("Listing all movies")
    try:
        logging.info('initializing Dapr client')
        movies = store.find_all()
        # remove prompt from the movie
        for movie in movies:
            if isinstance(movie, GeneratedMovie):
                movie.prompt = None
                #movie.payload = None
        # convert to JSON
        d_movies = [movie.to_json() for movie in movies]
        logging.info('Movies JSON: %s', d_movies)
        # return as JSON
        logging.info('Returning movies as JSON')
        return movies
    except Exception as e:
        logging.error('RuntimeError: %s', e)
        return Response(content=json.dumps([]), media_type="application/json", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@app.delete("/movies/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(movie_id: str):
    """Endpoint to delete a movie by ID."""
    logging.info("Deleting movie with ID: %s", movie_id)
    try:
        # Check if movie exists first
        movie = store.try_find_by_id(movie_id)
        if not movie:
            return Response(
                content=json.dumps({"error": "Movie not found"}),
                media_type="application/json",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Delete the movie
        success = store.delete(movie_id)
        if success:
            logging.info("Movie %s successfully deleted", movie_id)
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                content=json.dumps({"error": "Failed to delete movie"}),
                media_type="application/json",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    except Exception as e:
        logging.error('Delete_Movie Error: %s', e)
        logging.error('Call stack: %s', traceback.format_exc())
        return Response(
            content=json.dumps({'method': 'delete_movie', 'error': str(e)}),
            media_type="application/json",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
@app.get("/liveness")
def liveness():
    """
    Liveness probe endpoint.
    """
    #logging.info("Liveness probe")
    return Response(content=json.dumps({"status": "alive"}), media_type="application/json")

@app.get("/readiness")
def readiness():
    """
    Readiness probe endpoint.
    """
    #logging.info("Readiness probe")
    return Response(content=json.dumps({"status": "ready"}), media_type="application/json")

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8000)) 
    uvicorn.run(app, host="0.0.0.0", port=80)