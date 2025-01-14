""" A Rambi Flask app with a single route."""
from dataclasses import dataclass
import dataclasses
from typing import List
import logging
import os

from flask import Flask, render_template, request
from flask_wtf import FlaskForm
import uvicorn
from wtforms.validators import DataRequired
from wtforms import StringField, SubmitField
from dotenv import load_dotenv
from movie_service import TMDBService, Movie, GenAiMovieService
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
import openai


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Set the logging level to WARNING for the azure.core.pipeline.policies.http_logging_policy logger
http_logging_policy_logger = logging.getLogger('azure.core.pipeline.policies.http_logging_policy')
http_logging_policy_logger.setLevel(logging.WARNING)

# Set the logging level to WARNING for the urllib3.connectionpool logger
urllib3_logger = logging.getLogger('urllib3.connectionpool')
urllib3_logger.setLevel(logging.WARNING)

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
    return TMDBService(os.getenv("APIM_ENDPOINT"), api_key=os.getenv('API_SUBSCRIPTION_KEY'))


@ app.route('/env', methods=['GET', 'POST'])
def env():
    """Function printing python version."""
    return render_template('env.html', env=os.environ,github=GitHubContext())

@ app.route('/', methods=['GET', 'POST'])
def home():
    """Function printing python version."""
    twomovieform = TwoMoviesForm()
    rambimodel = None
    if twomovieform.validate_on_submit():
        tmdb_svc = tmdb_service()
        movie1 = tmdb_svc.get_movie_by_title(
            twomovieform.movie1Title.data)
        movie2 = tmdb_svc.get_movie_by_title(
            twomovieform.movie2Title.data)
        rambimodel = RambiModel(movie1, movie2)
    return render_template('index.html', form=twomovieform, rambimodel=rambimodel, github=GitHubContext())


@ app.route('/movie/poster_description', methods=['POST'])
def poster_description():
    """Function to show the movie poster description."""
    movie_title = request.form.get('movie_title')
    tmdb_svc = tmdb_service()
    movie = tmdb_svc.get_movie_by_title(movie_title)
    try:
        genai_movie_service = GenAiMovieService()
        poster_desc = genai_movie_service.describe_poster(movie.poster_url)
    except openai.OpenAIError as e:
        logger.error("Error in describe_poster: %s", e)
        poster_desc = f"Error in describe_poster: {e}"
    except Exception as e:
        logger.error("Other Error in describe_poster: %s", e)
        poster_desc = f"Error in describe_poster: {e}"

    return render_template('poster_description.html',
                           poster_description=poster_desc)


@app.route('/poster/generate', methods=['POST'])
def poster_generate():
    """Function to generate a new movie poster."""
    desc = request.form.get('poster_description')
    generated_poster = GenAiMovieService().generate_poster(desc)
    return render_template('poster.html', url=generated_poster)


@ app.route('/movie/generate', methods=['POST'])
def movie_generate():
    """Generate a new movie based on the two movies."""
    movie1_title = request.form.get('movie1Title')
    movie2_title = request.form.get('movie2Title')
    genre = request.form.get('genre')

    tmdb_svc = tmdb_service()
    movie1 = tmdb_svc.get_movie_by_title(movie1_title)
    movie2 = tmdb_svc.get_movie_by_title(movie2_title)

    genai_movie_service = GenAiMovieService()
    generated_movie = genai_movie_service.generate_movie2(movie1, movie2, genre)

    return render_template('generated_movie.html', generated_movie=generated_movie)


if __name__ == '__main__':
    uvicorn.run("app:app", host="0.0.0.0", port=5100)
