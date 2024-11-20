""" A simple Flask app with a single route."""
from dataclasses import dataclass
import dataclasses
import json

from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms import StringField, SubmitField
from flask import Flask, render_template, redirect, url_for, request
from dotenv import load_dotenv

from azurerambi.movie_service import MovieService, Movie

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'azure_rambi'


@dataclass
class Info:
    """ Data class for Info """
    title: str
    heading: str
    message: str


@dataclass
class RambiModel:
    """ Data class for RambiModel """
    movie1: Movie
    movie2: Movie

    def to_dict(self):
        return dataclasses.asdict(self)


class TwoMoviesForm(FlaskForm):
    """Form for find tow movies."""
    movie1Title = StringField('Movie 1', validators=[DataRequired()])
    movie2Title = StringField('Movie 2', validators=[DataRequired()])
    submit = SubmitField('Submit')


@app.route('/', methods=['GET', 'POST'])
def home():
    """Function printing python version."""
    twomovieform = TwoMoviesForm()
    rambimodel = None
    if twomovieform.validate_on_submit():
        movie_service = MovieService()
        movie1 = movie_service.get_movie_by_title(
            twomovieform.movie1Title.data)
        movie2 = movie_service.get_movie_by_title(
            twomovieform.movie2Title.data)
        rambimodel = RambiModel(movie1, movie2)

    return render_template('index.html', form=twomovieform, rambimodel=rambimodel)


@app.route('/movie/generate', methods=['POST'])
def movie_generate():
    """Generate a new movie based on the two movies."""
    movie1_title = request.form.get('movie1Title')
    movie2_title = request.form.get('movie2Title')
    movie_service = MovieService()
    movie1 = movie_service.get_movie_by_title(movie1_title)
    movie2 = movie_service.get_movie_by_title(movie2_title)
    generated_movie = movie_service.generate_movie(movie1, movie2)
    return render_template('generated_movie.html', generated_movie=generated_movie)


if __name__ == '__main__':
    app.run(debug=True)
