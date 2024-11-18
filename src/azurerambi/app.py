""" A simple Flask app with a single route."""
from flask import Flask,  render_template

app = Flask(__name__)


@app.route('/')
def home():
    """Function printing python version."""
    return render_template('index.html', title='Flask App',
                           heading='Welcome to my Flask App!',
                           message='This is a simple HTML template with variables.')


if __name__ == '__main__':
    app.run(debug=True)
