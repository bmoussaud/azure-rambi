import logging
from dotenv import load_dotenv
from azurerambi.movie_service import GenAiMovieService, Movie, TMDBService

#logging.basicConfig(level=logging.DEBUG)


load_dotenv()

movie1_title = "The Matrix"
movie2_title = "The Terminator"
genre = "comedy"

tmdb_svc = TMDBService()
movie1 = tmdb_svc.get_movie_by_title(movie1_title)
movie2 = tmdb_svc.get_movie_by_title(movie2_title)

genai_movie_service = GenAiMovieService()
generated_movie = genai_movie_service.generate_movie(movie1, movie2, genre)
print ("Generated movie: ", generated_movie)
