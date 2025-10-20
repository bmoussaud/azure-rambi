
from main import GenAiMovieService

title="The Blues Brothers" 
plot="Jake Blues, just released from prison, puts together his old band to save the Catholic home where he and his brother Elwood were raised."
genre="Action, Comedy, Crime, Music"
poster_url="https://image.tmdb.org/t/p/original//rhYJKOt6UrQq7JQgLyQcSWW5R86.jpg"

gen  = GenAiMovieService().describe_poster(title, poster_url)
print(gen)

print("generate poster  .......")
url = GenAiMovieService().generate_poster('benoit1', gen)
print(url)
