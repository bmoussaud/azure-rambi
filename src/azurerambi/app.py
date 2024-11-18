""" A simple Flask app with a single route."""
from dataclasses import dataclass

from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms import StringField, SubmitField
from flask import Flask, render_template, redirect, url_for, request


app = Flask(__name__)
app.config['SECRET_KEY'] = 'azure_rambi'


@dataclass
class Info:
    title: str
    heading: str
    message: str


class TwoMoviesForm(FlaskForm):
    """Form for find tow movies."""
    movie1Title = StringField('Movie 1', validators=[DataRequired()])
    movie2Title = StringField('Movie 2', validators=[DataRequired()])
    submit = SubmitField('Submit')


@app.route('/', methods=['GET', 'POST'])
def home():
    """Function printing python version."""
    twomovieform = TwoMoviesForm()
    if twomovieform.validate_on_submit():
        return redirect(url_for('success', movie1Title=twomovieform.movie1Title.data,
                                movie2Title=twomovieform.movie2Title.data))
    #    return redirect(url_for('success'))

    info = Info(title='Benoit Flask App', heading='BM Welcome to my Flask App!',
                message='This is a simple HTML template with variables.')

    return render_template('index.html', info=info, form=twomovieform)


@app.route('/success')
def success():
    """Function printing python version."""
    print("===== success.")
    print(request.args)
    movie1title = request.args.get('movie1Title')
    print(f"===== movie1Title {movie1title}.")
    movie2title = request.args.get('movie2Title')
    print(f"===== movie2Title {movie2title}.")
    return f"Movie 1: {movie1title}, Movie 2: {movie2title}."


if __name__ == '__main__':
    app.run(debug=True)
