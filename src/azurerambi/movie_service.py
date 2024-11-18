""" Class to manage the access to TMDB API """
from dataclasses import dataclass
from tmdbv3api import Search


@dataclass
class Movie:
    """ Data class for Movie """
    title: str
    plot: str
    poster_url: str


class MovieService:
    """ Class to manage the access to TMDB API """

    def __init__(self):
        pass

    def get_movie_by_title(self, title) -> Movie:
        """ Get movie info from TMDB API """
        search_results = Search().movies(title)
        if search_results:
            sr = search_results[0]  # Return the first result
            return Movie(sr.title,
                         sr.overview,
                         f"https://image.tmdb.org/t/p/original/{sr.poster_path}")
        else:
            return None
