
from main import GenAiMovieService
service = GenAiMovieService()
movie_id = "9392_22_Science Fiction_51894"
genmovie = service.get_generated_movie(movie_id)
print(genmovie)

print("generate poster  .......")
url = service.generate_poster_gpt_image_edit(movie_id)
print(url)

import sys
sys.exit(0)

title="The Blues Brothers" 
plot="Jake Blues, just released from prison, puts together his old band to save the Catholic home where he and his brother Elwood were raised."
genre="Action, Comedy, Crime, Music"
poster_url="https://image.tmdb.org/t/p/original//rhYJKOt6UrQq7JQgLyQcSWW5R86.jpg"

gen  = GenAiMovieService().describe_poster(title, poster_url)
print(gen)

print("generate poster  .......")
url = GenAiMovieService().generate_poster_gpt_image('benoit1', "3 ecureuils dans la foret, style dessin anime")
print(url)
