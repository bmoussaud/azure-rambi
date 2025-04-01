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
from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.instrumentation.flask import FlaskInstrumentor

from wtforms.validators import DataRequired
from wtforms import StringField, SubmitField
from dotenv import load_dotenv
from movie_service import TMDBService, Movie
from movie_poster_client import MoviePosterClient


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


if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING") is not None:
    logger.info("configure_azure_monitor")
    configure_azure_monitor()

logger.info("Instrumenting Flask app")
FlaskInstrumentor().instrument_app(app)


genre_list = ["Action", "Adventure", "Animation","Comedy", "Crime",
              "Documentary", "Drama","Family", "Fantasy", "History", "Horror",
              "Music", "Mystery", "Romance", "Science Fiction",
              "TV Movie", "Thriller", "War", "Western"]

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
    return render_template('index.html', form=twomovieform, rambimodel=rambimodel, github=GitHubContext())


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
        logger.error("Other Error in describe_poster: %s", e)
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
            "genre": genre
        }
        logger.info("data: %s", json.dumps(data, indent=2))
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
            
        except requests.RequestException as e:
            logger.error("Error in calling movie_generate service: %s", e)
            generated_movie = {
                "title": "Generation Movie Error",
                "plot": f"Error in calling movie_generate service: {e}",
                "poster_url": ""
            }
        return render_template('generated_movie.html', generated_movie=generated_movie)


if __name__ == '__main__':
    app.run( debug=True)
