""" A Rambi Flask app with a single route."""
from dataclasses import dataclass
import dataclasses
from typing import List
import logging
import os
import requests
import json
import random
import uvicorn
import base64

from collections import OrderedDict
from flask import Flask, render_template, request, jsonify, session
from flask_wtf import FlaskForm
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.instrumentation.flask import FlaskInstrumentor

from wtforms.validators import DataRequired
from wtforms import StringField, SubmitField
from dotenv import load_dotenv
from movie_service import TMDBService, Movie
from movie_poster_client import MoviePosterClient
from dapr.clients import DaprClient


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Set the logging level to WARNING for the azure.core.pipeline.policies.http_logging_policy logger
logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
logging.getLogger('azure.monitor.opentelemetry.exporter').setLevel(logging.WARNING)

# Set the logging level to WARNING for the urllib3.connectionpool logger
logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'azure_rambi'
app.config['SESSION_TYPE'] = 'filesystem'


if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING") is not None:
    logger.info("configure_azure_monitor")
    configure_azure_monitor()

# Only instrument if not already instrumented
if not hasattr(app, '_instrumented'):
    logger.info("Instrumenting Flask app")
    FlaskInstrumentor().instrument_app(app)
    app._instrumented = True


genre_list = ["Action", "Adventure", "Animation","Comedy", "Crime",
              "Documentary", "Drama","Family", "Fantasy", "History", "Horror",
              "Music", "Mystery", "Romance", "Science Fiction",
              "TV Movie", "Thriller", "War", "Western"]

language_list = ["english", "french", "spanish", "german", "italian"]

movie_poster_client = MoviePosterClient()


@dataclass
class GitHubContext:
    """ Data class for GitHubContext """
    job: str = os.getenv('GITHUB_JOB')
    sha: str = os.getenv('GITHUB_SHA')
    actor: str = os.getenv('GITHUB_ACTOR')
    run_number: str = os.getenv('GITHUB_RUN_NUMBER')
    repository: str = "https://github.com/bmoussaud/azure-rambi"

@dataclass
class RambiModel:
    """ Data class for RambiModel """
    movie1: Movie
    movie2: Movie
    default_genres: List[str] = dataclasses.field(default_factory=lambda: genre_list)
    languages: List[str] = dataclasses.field(default_factory=lambda: language_list)
    
class TwoMoviesForm(FlaskForm):
    """Form for find tow movies."""
    movie1Title = StringField('Movie 1', validators=[DataRequired()])
    movie2Title = StringField('Movie 2', validators=[DataRequired()])
    submit = SubmitField('Submit')

def tmdb_service() -> TMDBService:
    """ Function to get the TMDBService """
    return TMDBService(os.getenv("TMDB_ENDPOINT"), api_key=os.getenv('APIM_SUBSCRIPTION_KEY'))

@ app.route('/env', methods=['GET', 'POST'])
def env():
    """Function printing python version."""
    sorted_env = OrderedDict(sorted(os.environ.items()))
    return render_template('env.html', env=sorted_env, github=GitHubContext())

@ app.route('/', methods=['GET', 'POST'])
def home():
    """Function printing python version."""
    twomovieform = TwoMoviesForm()
    rambimodel = None
    if (twomovieform.validate_on_submit()):
        tmdb_svc = tmdb_service()
        movie1 = tmdb_svc.get_movie_by_title(
            twomovieform.movie1Title.data)
        movie2 = tmdb_svc.get_movie_by_title(
            twomovieform.movie2Title.data)
        rambimodel = RambiModel(movie1, movie2)
    
    # Get current language preference, default to 'english' if not set
    current_language = session.get('preferred_language', 'english')
    return render_template('index.html', form=twomovieform, rambimodel=rambimodel, 
                           current_language=current_language, languages=language_list,
                           github=GitHubContext())


@ app.route('/poster/description', methods=['POST'])
def poster_description():
    """Function to show the movie poster description."""
    logger.info("poster_description")
    movie_id = request.form.get('movie_id')
    try:
        tmdb_svc = tmdb_service()
        logger.info("getting movie by id: %s", movie_id)
        movie = tmdb_svc.get_movie_by_id(movie_id)
        logger.info("movie: %s", movie)
        logger.info("movie.poster_url: %s", movie.poster_url)
        logger.info("movie.title: %s", movie.title)
        poster_desc = movie_poster_client.describe_poster(movie.title, movie.poster_url)
    except Exception as e:
        logger.exception("Other Error in describe_poster")
        poster_desc = f"Error in describe_poster: {e}"

    return render_template('poster_description.html',
                           poster_description=poster_desc)


@app.route('/poster/generate', methods=['POST'])
def poster_generate():
    """Function to generate a new movie poster."""
    logger.info("poster_generate")
    desc = request.form.get('poster_description')
    movie_id = request.form.get('movie_id')
    logger.info("* movie_id: %s", movie_id)
    logger.info("* desc: %s", desc)
    
    generated_poster = movie_poster_client.generate_poster(movie_id, desc)
    return render_template('poster.html', url=generated_poster['url'], error=generated_poster['error'])

@app.route('/poster/<movie_id>.png', methods=['GET'])
def poster(movie_id:str):
    """Function to show the movie poster."""
    logger.info("poster %s", movie_id)
    url = movie_poster_client.redirect_poster_url(movie_id)
    logger.info("url: %s", url)
    #stream the content of the url
    response = requests.get(url, stream=True, timeout=100)
    logger.info("response: %s", response)
    if response.status_code != 200:
        return f"Failed to retrieve the image. /poster/{movie_id}.png", response.status_code
    def generate():
        for chunk in response.iter_content(chunk_size=8192):
            yield chunk
    return app.response_class(generate(), content_type=response.headers['Content-Type'])

ui_design = os.getenv("UI_DESIGN", "xxx")
@ app.route('/movie/generate', methods=['POST'])
def movie_generate():
    """Generate a new movie based on the two movies."""
    logger.info("movie_generate")
    if ui_design == "bootstrap":
        generated_movie = Movie(title="Barb-a-Bambi: Forest Frenzy",
            plot="In this high-octane adventure, the enchanted forest is in jeopardy, and it’s up to Bambi and the Barbapapa family to save their home. Young prince Bambi, alongside his ever-energetic friends Thumper and Flower, embarks on a mission to rally all the forest creatures. They are joined by the shape-shifting Barbapapa family, each member bringing a unique ability essential for confronting the impending threat. As they race against time, Bambi must learn to harness leadership beyond his fawnhood, while the Barbapapas morph into incredible tools and forms, aiding in the action-packed and comical rescue mission. Together, they discover the true strength of unity and creativity in the face of adversity, ensuring the woods remain a vibrant, peaceful sanctuary for all.",
            poster_url="",
            poster_description="A poster of a deer and a pink blob")
        return render_template('generated_movie.html', generated_movie=generated_movie)
    else:
        movie1_id = request.form.get('movie1Id')
        logger.info("movie1_id: %s", movie1_id)
        movie2_id = request.form.get('movie2Id')
        logger.info("movie2_id: %s", movie2_id)

        genre = request.form.get('genre')
        # Use language from session if available, otherwise use the form data or default to 'english'
        language = session.get('preferred_language') or 'english'
        logger.info("Using language: %s", language)
        tmdb_svc = tmdb_service()
        movie1 = tmdb_svc.get_movie_by_id(movie1_id)
        logger.info("movie1: %s", movie1)
        movie2 = tmdb_svc.get_movie_by_id(movie2_id)
        logger.info("movie2: %s", movie2)
        endpoint = os.getenv("MOVIE_GENERATOR_ENDPOINT","http://movie-generator-svc")
        logger.info("Calling movie_generate service at %s", endpoint)
        data = {
            "movie1": movie1.model_dump(),
            "movie2": movie2.model_dump(),
            "genre": genre,
            "language": language
        }
        logger.info("movie generate data: %s", json.dumps(data, indent=2))
        try:
            response = requests.post(
                f"{endpoint}/generate",
                json=data,
                timeout=1000
            )
            response.raise_for_status()
            generated_movie = response.json()
            genre_index = genre_list.index(genre) if genre in genre_list else -1
            #generate the generated movie id
            if 'id' not in generated_movie:
                logger.error("!!!! No id in generated movie, generating one")
                generated_movie['id'] = f"{genre_index}_{movie1_id}_{movie2_id}_{random.randint(10000, 99999)}"

            logger.info("Generated movie: %s", json.dumps(generated_movie, indent=2))
            with DaprClient() as d:
                logger.info("Invoke movie gallery service to save the generated movie")
                d.invoke_method(
                    app_id="movie-gallery-svc",
                    method_name="movies",
                    data=json.dumps(generated_movie),
                    http_verb='POST'
                )
        except Exception as e:
            logger.exception("Exception in calling movie_generate service")
            generated_movie = {
                "title": "Generation Movie Error",
                "plot": f"Error in calling movie_generate service: {e}",
                "poster_url": ""
            }
        return render_template('generated_movie.html', generated_movie=generated_movie)

@app.route('/gallery', methods=['GET'])
def movie_gallery():
    """Display all movies from the movie gallery service."""
    logger.info("Accessing movie gallery")
    movies = []
    try:
        with DaprClient() as d:
            logger.info("Invoking movie gallery service to get all movies")
            resp = d.invoke_method(
                app_id="movie-gallery-svc",
                method_name="movies",
                http_verb='GET'
            )
            logging.info(f"Response from movie gallery service: {resp}")
            # Properly access data from Dapr InvokeMethodResponse object
            if resp.data:
                movies = json.loads(resp.data.decode('utf-8'))
                logger.info(f"Retrieved {len(movies)} movies from gallery")
                
                # Fetch validation scores for each movie
                for movie in movies:
                    if 'id' in movie:
                        validation_scores = movie_poster_client.get_validation_scores(movie['id'])
                        if validation_scores:
                            movie['validation_scores'] = validation_scores
                            logger.info(f"Added validation scores for movie {movie['id']}: overall_score={validation_scores.get('overall_score', 'N/A')}")
                        else:
                            logger.info(f"No validation scores found for movie {movie['id']}")
                    else:
                        logger.warning(f"Movie missing 'id' field: {movie}")
            else:
                logger.warning("No data returned from movie gallery service")
    except Exception as e:
        logger.exception("Error retrieving movies from gallery service", exc_info=e)
        
    return render_template('gallery.html', movies=movies, github=GitHubContext())

@app.route('/delete_movie/<movie_id>', methods=['DELETE'])
def delete_movie(movie_id):
    """Delete a movie from the gallery."""
    logger.info(f"Deleting movie with ID: {movie_id}")
    try:
        with DaprClient() as d:
            logger.info("Invoking movie gallery service to delete movie")
            resp = d.invoke_method(
                app_id="movie-gallery-svc",
                method_name=f"movies/{movie_id}",
                http_verb='DELETE'
            )
            
            if resp.status_code == 204:
                logger.info(f"Successfully deleted movie {movie_id}")
                return jsonify({"status": "success", "message": "Movie deleted successfully"})
            elif resp.status_code == 404:
                logger.warning(f"Movie {movie_id} not found")
                return jsonify({"status": "error", "message": "Movie not found"}), 404
            else:
                logger.error(f"Failed to delete movie {movie_id}, status code: {resp.status_code}")
                return jsonify({"status": "error", "message": "Failed to delete movie"}), 500
                
    except Exception as e:
        logger.exception("Error deleting movie from gallery service", exc_info=e)
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route('/set_language', methods=['POST'])
def set_language():
    """Set user language preference"""
    selected_language = request.form.get('language')
    logger.info(f"Setting language preference to: {selected_language}")
    
    if selected_language in language_list:
        session['preferred_language'] = selected_language
        return jsonify({"status": "success", "language": selected_language})
    else:
        return jsonify({"status": "error", "message": "Invalid language selection"}), 400

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5555))
    app.run(debug=True, port=port, host='0.0.0.0')
