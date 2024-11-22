""" Class to manage the access to TMDB API """
import os
import json

from dataclasses import dataclass
from pydantic import BaseModel
from tmdbv3api import Search
from openai import AzureOpenAI
import openai

from dc_schema import get_schema

# openai.log = "debug"


@dataclass
class Movie:
    """ Data class for Movie """
    title: str
    plot: str
    poster_url: str
    poster_description: str = None


class Movie2(BaseModel):
    """ Data class for Movie2 """
    title: str
    plot: str
    poster_url: str
    poster_description: str = None
    

@dataclass
class GenAIMovie(Movie2):
    """ Data class for GenAIMovie """
    prompt: str = None


class TMDBService:
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


class GenAiMovieService:
    """ Class to manage the access to OpenAI API to generate a new movie """

    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2024-08-01-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )

    def describe_poster(self, poster_url: str) -> str:
        """describe the movie poster using gp4o model"""
        response = self.client.chat.completions.create(
            model="gpt4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": [
                    {
                        "type": "text",
                        "text": "Describe this movie poster:"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                                "url": poster_url
                        }
                    }
                ]}
            ],
            max_tokens=2000
        )
        # Return the generated description
        print(
            f"--{poster_url} describe_poster: {response.choices[0].message.content}.\n")

        return response.choices[0].message.content

    def generate_poster(self, poster_description: str) -> str:
        """ Generate a new movie poster based on the description """
        print(f"generate_poster called with {poster_description}.\n")
        try:
            client = AzureOpenAI()
            response = client.images.generate(
                model="dall-e-3",
                prompt="Generate a movie poster with this image description: "+poster_description,
                n=1,
                size='1024x1792'
            )
            json_response = json.loads(response.model_dump_json())
            url = json_response["data"][0]["url"]
        except Exception as e:
            print(f"--- Generation Image Error: {e}")
            url = "https://placehold.co/150x220/red/white?text=Image+Not+Available"
        return url

    def generate_movie(self, movie1: Movie, movie2: Movie, genre: str) -> Movie:
        """ Generate a new movie based on the two movies """
        print(
            "generate_movie called based on two movies {movie1.title} and {movie2.title} {genre}!!.\n")

        movie1.poster_description = self.describe_poster(movie1.poster_url)
        movie2.poster_description = self.describe_poster(movie2.poster_url)

        movie_schema = json.dumps(get_schema(Movie), indent=2)
        # print(movie_schema)

        # https://yh3bek4jwqde2-openai.openai.azure.com/openai/deployments/gpt4o/chat/completions?api-version=2024-08-01-preview

        with open("prompts/new_movie.txt", "r", encoding="utf-8") as file:
            prompt_template = file.read()

        prompt = prompt_template.format(
            movie1_title=movie1.title,
            movie1_plot=movie1.plot,
            movie1_description=movie1.poster_description,
            movie2_title=movie2.title,
            movie2_plot=movie2.plot,
            movie2_description=movie2.poster_description,
            genre=genre,
            format=movie_schema
        )

        print(prompt)

        completion = self.client.chat.completions.create(
            model="gpt4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a bot expert with a huge knowledge about movies and the cinema."
                },
                {
                    "role": "user",
                    "content": prompt
                },
            ]
        )
        generated_movie_plot = completion.choices[0].message.content
        # print("Generated movie plot: ", generated_movie_plot)
        # Deserialize the generated movie plot into a Movie object using generated_movie_plot
        new_movie = json.loads(generated_movie_plot)
        new_movie["poster_url"] = None
        new_movie["prompt"] = prompt
        return new_movie
    
    def generate_movie2(self, movie1: Movie, movie2: Movie, genre: str) -> Movie:
        """ Generate a new movie based on the two movies 
        https://openai.com/index/introducing-structured-outputs-in-the-api/
        """
        print(
            f"generate_movie called based on two movies {movie1.title} and {movie2.title} {genre}!!.\n")

        movie1.poster_description = self.describe_poster(movie1.poster_url)
        movie2.poster_description = self.describe_poster(movie2.poster_url)

        with open("prompts/structured_new_movie_short.txt", "r", encoding="utf-8") as file:
            prompt_template = file.read()

        #print("Prompt template: ", prompt_template)

        prompt = prompt_template.format(
            movie1_title=movie1.title,
            movie1_plot=movie1.plot,
            movie1_description=movie1.poster_description,
            movie2_title=movie2.title,
            movie2_plot=movie2.plot,
            movie2_description=movie2.poster_description,
            genre=genre
        )

        #print(prompt)

        completion = self.client.beta.chat.completions.parse(
            model="gpt4o",
            response_format=GenAIMovie,
            messages=[
                {
                    "role": "system",
                    "content": "You are a bot expert with a huge knowledge about movies and the cinema."
                },
                {
                    "role": "system",
                    "content": """
                                Two movie titles and plots will be provided, along with a target genre.
                                Using the titles, plots and genre as inspiration, generate the following:
                                * Generate a new movie title that combines elements of the provided titles and fits the target genre. The title should be catchy and humorous.
                                * Generate a 4-6 sentence movie plot synopsis for the new title, incorporating themes, characters, or plot points from the provided movies. Adapt them to fit the target genre.
                                * Based on the generated movie plot and the 2 provied movie posters, describe a movie poster
                                Take care of not generating any violence. 
                                Take care of not generating any copyrighted content. 
                                Remove all mentions about copyrighted content and replace them with the generic words.  
                                """
                },
                {
                    "role": "user",
                    "content": prompt
                },
            ]
        )
        message = completion.choices[0].message
        #print("Message: ", message)
        #print("Message Content: ", message.content)
        movie = GenAIMovie.model_validate(json.loads(message.content))
        movie.prompt= prompt
        movie.poster_url = None
        return movie


