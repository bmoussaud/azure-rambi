""" A simple Flask app with a single route."""
from dataclasses import dataclass
import dataclasses
from typing import List

#import logging

from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms import StringField, SubmitField
from flask import Flask, render_template, request
from dotenv import load_dotenv
from azurerambi.movie_service import GenAiMovieService, Movie, TMDBService
# logging.basicConfig(level=logging.DEBUG)


load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'azure_rambi'



@dataclass
class RambiModel:
    """ Data class for RambiModel """
    movie1: Movie
    movie2: Movie
    default_genres: List[str] = dataclasses.field(default_factory=lambda: ["Action", "Adventure", "Animation",
                                                                           "Comedy", "Crime",
                                                                           "Documentary", "Drama",
                                                                           "Family", "Fantasy", "History", "Horror",
                                                                           "Music", "Mystery", "Romance", "Science Fiction",
                                                                           "TV Movie", "Thriller", "War", "Western"])


class TwoMoviesForm(FlaskForm):
    """Form for find tow movies."""
    movie1Title = StringField('Movie 1', validators=[DataRequired()])
    movie2Title = StringField('Movie 2', validators=[DataRequired()])
    submit = SubmitField('Submit')


@ app.route('/', methods=['GET', 'POST'])
def home():
    """Function printing python version."""
    twomovieform = TwoMoviesForm()
    rambimodel = None
    if twomovieform.validate_on_submit():
        tmdb_svc = TMDBService()
        movie1 = tmdb_svc.get_movie_by_title(
            twomovieform.movie1Title.data)
        movie2 = tmdb_svc.get_movie_by_title(
            twomovieform.movie2Title.data)
        rambimodel = RambiModel(movie1, movie2)

    return render_template('index.html', form=twomovieform, rambimodel=rambimodel)


@ app.route('/movie/poster_description', methods=['POST'])
def poster_description():
    """Function to show the movie poster description."""
    movie_title = request.form.get('movie_title')
    tmdb_svc = TMDBService()
    movie = tmdb_svc.get_movie_by_title(movie_title)
    genai_movie_service = GenAiMovieService()
    poster_desc = genai_movie_service.describe_poster(movie.poster_url)
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

    tmdb_svc = TMDBService()
    movie1 = tmdb_svc.get_movie_by_title(movie1_title)
    movie2 = tmdb_svc.get_movie_by_title(movie2_title)

    genai_movie_service = GenAiMovieService()
    generated_movie = genai_movie_service.generate_movie2(movie1, movie2, genre)
    return render_template('generated_movie.html', generated_movie=generated_movie)



if __name__ == '__main__':
    app.run(debug=True)
