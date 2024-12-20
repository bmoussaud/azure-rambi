""" Unit tests for the MoviePosterClient class """

import logging
from azurerambi.movie_poster import MoviePosterClient
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
#handler = logging.StreamHandler(sys.stdout)
#logger.addHandler(handler)

load_dotenv()


def test_describe_poster_success():
    """Test the describe_poster method with a successful response."""
    desc = MoviePosterClient().describe_poster("Wild Wild West", "https://image.tmdb.org/t/p/original//3C5cZnIwQ6Wj4qGFKv0BBjimWro.jpg")
    print(desc)


def test_generate_poster_failure():
    """Test the generate_poster method with a failed response."""
    desc = """
    The poster features a colorful desert landscape with towering mesas and a whimsical roller coaster made of metal parts spiraling through the foreground. In the center, a jovial group of rustic yet eccentric characters, each with unique and vibrant attire, crowds around a mechanical contraption, beaming with pride and delightful confusion. The sky above is painted in soft pastel hues, creating a heartwarming and adventurous atmosphere. The ensemble's expressions and dynamic poses emphasize their tight-knit bond and zest for life, perfectly capturing the comedic and family-centric adventure of the film.
    """
    url  = MoviePosterClient().generate_poster(desc)
    print(url)
       
#test_describe_poster_success()
#test_generate_poster_failure()