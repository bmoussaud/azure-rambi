import httpx
import asyncio  
import os
from agent import PosterValidationAgent
from entities import PosterValidationRequest
from dotenv import load_dotenv


load_dotenv()
async def main():
 
    poster_agent = PosterValidationAgent()
    await poster_agent.create_agent()
    movie_id="744_346698_Animation_99648"

    url = f"{os.getenv("MOVIE_GALLERY_ENDPOINT")}/movies/{movie_id}"
    print(url)
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        print("Movie Gallery Response:", response.status_code, response.text)
        response.raise_for_status()
        response_json = response.json()
        print("Movie Gallery JSON Response:", response_json)

        request = PosterValidationRequest(
            poster_url=response_json.get("internal_poster_url"),
            poster_description=response_json.get("poster_description"),
            movie_id=movie_id,
            movie_title=response_json.get("title"),
            movie_genre=response_json.get("genre"),
            language="French"
        )
        print("Poster Validation Request:", request)
        response = await poster_agent.validate_poster(request=request)
        #print(response)
        import json
        print(response.model_dump_json(indent=2))

if __name__ == "__main__":
    asyncio.run(main())