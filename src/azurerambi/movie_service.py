""" Class to manage the access to TMDB API """
import os
import json

from dataclasses import dataclass
from tmdbv3api import Search
from openai import AzureOpenAI
import openai

from dc_schema import get_schema

openai.log = "debug"


@dataclass
class Movie:
    """ Data class for Movie """
    title: str
    plot: str
    poster_url: str
    poster_description: str = None


@dataclass
class GenAIMovie(Movie):
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
                        "text": "Describe this picture:"
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

    def generate_poster(self, posterDescription: str) -> str:
        """ Generate a new movie poster based on the description """
        print(
            f"----generate_movie_poster called with {posterDescription}!!.\n")
        try:
            client = AzureOpenAI()
            response = client.images.generate(
                model="dall-e-3",
                prompt=posterDescription,
                n=1,
                size='1024x1792'
            )
            json_response = json.loads(response.model_dump_json())
            url = json_response["data"][0]["url"]
        except Exception as e:
            print(f"--- Generation Image Error: {e}")
            url = "https://bit.ly/3YOrHPI"
        return url

    def generate_movie(self, movie1: Movie, movie2: Movie) -> Movie:
        """ Generate a new movie based on the two movies """
        print(
            "generate_movie called based on two movies {movie1.title} and {movie2.title}")

        movie1.poster_description = self.describe_poster(movie1.poster_url)
        movie2.poster_description = self.describe_poster(movie2.poster_url)

        movie_schema = json.dumps(get_schema(Movie), indent=2)
        print(movie_schema)

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
            genre="comedy",
            format=movie_schema
        )

        print(prompt)

        completion = self.client.chat.completions.create(
            model="gpt4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a bot expert with a huge knowledge in movies and cinema."
                },
                {
                    "role": "user",
                    "content": f"Generate a movie poster with this description: {prompt}"
                },
            ]
        )
        generated_movie_plot = completion.choices[0].message.content

        print("Generated movie plot: ", generated_movie_plot)

        # Deserialize the generated movie plot into a Movie object using generated_movie_plot
        new_movie = json.loads(generated_movie_plot)
        url = self.generate_poster(new_movie.get("poster_description"))
        new_movie["poster_url"] = url
        new_movie["prompt"] = prompt
        return new_movie
