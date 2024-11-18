""" A simple Flask app with a single route."""
from dataclasses import dataclass

from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms import StringField, SubmitField
from flask import Flask, render_template, redirect, url_for, request

from azurerambi.movie_service import MovieService, Movie
from dotenv import load_dotenv

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
    """ Data class for PairOfMovies """
    movie1: Movie
    movie2: Movie


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


@app.route('/success')
def success():
    """Function printing python version."""
    print("===== success.")
    print(request.args)
    movie1 = request.args.get('movie1')
    print(f"===== movie1Title {movie1.title}.")
    movie2 = request.args.get('movie2')
    print(f"===== movie2Title {movie2.title}.")
    return f"Movie 1: {movie1.title}, Movie 2: {movie2.title}."


if __name__ == '__main__':
    app.run(debug=True)
