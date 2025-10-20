
from main import GenAiMovieService, GenAIMovie, Movie, MoviePayload

movie1 = Movie(id="525",
               title="The Blues Brothers", 
               plot="Jake Blues, just released from prison, puts together his old band to save the Catholic home where he and his brother Elwood were raised.", 
               genre="Action, Comedy, Crime, Music", 
               poster_url="https://image.tmdb.org/t/p/original//rhYJKOt6UrQq7JQgLyQcSWW5R86.jpg",
               poster_description= "The movie poster for \"The Blues Brothers\" features a gradient blue background with the title prominently displayed at the top in white and blue lettering. Below the title, two men are depicted wearing classic black suits, white dress shirts, and black ties, accessorized with black fedora hats and sunglasses. The man on the left is slightly taller and has one arm around the shoulder of the man on the right, creating a sense of camaraderie and partnership typical of the iconic duo. The overall style suggests elements of comedy and coolness associated with the characters.")

movie2 = Movie(id="268153",
              title="La naissance des Barbapapa", 
              plot="The Barbapapas are creatures that can change their form, and those are the adventures is this unusual family in his struggle to find his place in the planet while helping other people and animals", 
              poster_url="https://image.tmdb.org/t/p/original//mud7GBjqqLxVjOcGEftc84BAFfU.jpg",
              poster_description="The poster for La naissance des Barbapapa features a joyful and colorful design. In the center, there is a large, smiling pink character with a rounded shape and simple facial features, representative of the Barbapapa character. Surrounding this central figure are other characters from the Barbapapa family, each in different colors such as blue, orange, black, red, yellow, green, and purple. These characters have unique expressions and postures, adding to the whimsical and lively feel of the poster. \\n\\nThe background is a bright pink with a subtle gradient, featuring white line illustrations that resemble abstract, leafy shapes.")

gen  = GenAiMovieService().generate_movie(movie1, movie2, "Animation")
print("--------------------")
print("TITLE",gen.title)
print("PLOT", gen.plot)
print("DESCRIPTION", gen.poster_description)
