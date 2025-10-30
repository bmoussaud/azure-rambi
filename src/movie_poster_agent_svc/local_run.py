import httpx
import asyncio  
import os
import logging
from agent import PosterValidationAgent
from entities import PosterValidationRequest
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

load_dotenv()



async def main_structured():
 
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

async def main():
 
    poster_agent = PosterValidationAgent()
    await poster_agent.create_agent()
    
    movie_id="744_346698_Animation_99648"

    url = f"{os.getenv("MOVIE_GALLERY_ENDPOINT")}/movies/{movie_id}"
    logger.info(url)
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        logger.info(f"Movie Gallery Response:{response.status_code}, {response.text}")
        response.raise_for_status()
        response_json = response.json()
        logger.info(f"Movie Gallery JSON Response: {response_json}")
        response = await poster_agent.validate_poster_str(str(response_json), language="French", store_validation=True)
        import json
        logger.info(response.model_dump_json(indent=2))

async def main_event():
    poster_agent = PosterValidationAgent()
    await poster_agent.create_agent()
    
    data ="""
     {"data":"\"{\\\"id\\\":\\\"3170_744_Romance_57210\\\",\\\"title\\\":\\\"Wings of the Heart\\\",\\\"plot\\\":\\\"In the lush Evergreen Forest, Bella, a graceful young deer, dreams of seeing the world beyond her woodland home. When a charismatic flight instructor named Max arrives to teach the forest creatures the art of gliding, Bella enrolls in his classes, eager to fulfill her dreams. As Bella and Max spend time together soaring above the treetops, they develop a deep and heartfelt connection. Together, they navigate the joys and challenges of learning to fly, discovering that love can lift them to new heights. Their blossoming romance inspires the entire forest community, proving that with courage and companionship, any dream is within reach.\\\",\\\"poster_url\\\":\\\"/poster/3170_744_Romance_57210.png\\\",\\\"internal_poster_url\\\":\\\"https://azrambi6pu4zfbazzx5a.blob.core.windows.net/movieposters/3170_744_Romance_57210.png\\\",\\\"poster_description\\\":\\\"The poster showcases a serene forest backdrop with vibrant green foliage under a clear blue sky. In the foreground, a graceful deer with gentle eyes looks upward towards a colorful butterfly, symbolizing hope and dreams. Standing beside her is a charming individual dressed in a stylish flight jacket, exuding warmth and confidence. Above them, delicate gliders soar gracefully, blending seamlessly with the natural landscape. Soft sunlight filters through the trees, casting a romantic glow over the scene. The overall composition conveys themes of love, adventure, and the beauty of pursuing one's aspirations together.\\\",\\\"prompt\\\":\\\"### Movie 1\\\\n\\\\n* Title: Bambi\\\\n* Plot: Bambi's tale unfolds from season to season as the young prince of the forest learns about life, love, and friends.\\\\n* Poster description: \\\\\\\"The \\\\\\\\\\\\\\\"Bambi\\\\\\\\\\\\\\\" movie poster is vibrant and artistic, capturing the charm of the beloved Disney film. It prominently features a close-up of Bambi, the young deer, with wide, expressive eyes looking up towards a colorful butterfly fluttering nearby. Bambi is depicted in warm shades of brown and orange, highlighting his gentle innocence.\\\\\\\\n\\\\\\\\nThe background features lush green foliage, exemplifying the natural forest setting of the movie. Surrounding Bambi are his forest friends, including Flower the skunk and Thumper the rabbit, both of which look excited and are gazing upwards with cheerful expressions. Towards the right side of the image, Bambi\\u2019s father, the Great Prince of the Forest, stands tall and regal, symbolizing strength and guidance.\\\\\\\\n\\\\\\\\nThe word \\\\\\\\\\\\\\\"Bambi\\\\\\\\\\\\\\\" is elegantly written in vertical orientation along the side of the poster, making it a focal point as it balances the composition. The poster beautifully encapsulates the spirit of adventure, friendship, and the beauty of nature that \\\\\\\\\\\\\\\"Bambi\\\\\\\\\\\\\\\" represents.\\\\\\\"\\\\n\\\\n### Movie 2\\\\n\\\\n* Title: Top Gun\\\\n* Plot: For Lieutenant Pete 'Maverick' Mitchell and his friend and co-pilot Nick 'Goose' Bradshaw, being accepted into an elite training school for fighter pilots is a dream come true. But a tragedy, as well as personal demons, will threaten Pete's dreams of becoming an ace pilot.\\\\n* Poster description: \\\\\\\"The \\\\\\\\\\\\\\\"Top Gun\\\\\\\\\\\\\\\" movie poster features a striking design with two individuals wearing military-style jackets, one of which prominently displays various patches, including a winged emblem and insignias related to aviation and military service. The background showcases the American flag with its recognizable red stripes and white stars, providing a patriotic theme that aligns with the film's focus on elite fighter pilots. The movie\\u2019s title, \\\\\\\\\\\\\\\"Top Gun,\\\\\\\\\\\\\\\" is boldly displayed across the center in large, white capital letters, featuring a stylized white star underneath and flanked by horizontal red stripes, evoking imagery related to aviation and speed. The overall composition conveys themes of action, patriotism, and military aviation.\\\\\\\"\\\\n\\\\n### Additional Information\\\\n\\\\n* Target Genre: Romance \\\\n* Output language: english\\\\n\\\\n\\\\n\\\",\\\"payload\\\":{\\\"movie1\\\":{\\\"id\\\":\\\"3170\\\",\\\"title\\\":\\\"Bambi\\\",\\\"plot\\\":\\\"Bambi's tale unfolds from season to season as the young prince of the forest learns about life, love, and friends.\\\",\\\"poster_url\\\":\\\"https://image.tmdb.org/t/p/original//wV9e2y4myJ4KMFsyFfWYcUOawyK.jpg\\\",\\\"internal_poster_url\\\":null,\\\"poster_description\\\":\\\"\\\\\\\"The \\\\\\\\\\\\\\\"Bambi\\\\\\\\\\\\\\\" movie poster is vibrant and artistic, capturing the charm of the beloved Disney film. It prominently features a close-up of Bambi, the young deer, with wide, expressive eyes looking up towards a colorful butterfly fluttering nearby. Bambi is depicted in warm shades of brown and orange, highlighting his gentle innocence.\\\\\\\\n\\\\\\\\nThe background features lush green foliage, exemplifying the natural forest setting of the movie. Surrounding Bambi are his forest friends, including Flower the skunk and Thumper the rabbit, both of which look excited and are gazing upwards with cheerful expressions. Towards the right side of the image, Bambi\\u2019s father, the Great Prince of the Forest, stands tall and regal, symbolizing strength and guidance.\\\\\\\\n\\\\\\\\nThe word \\\\\\\\\\\\\\\"Bambi\\\\\\\\\\\\\\\" is elegantly written in vertical orientation along the side of the poster, making it a focal point as it balances the composition. The poster beautifully encapsulates the spirit of adventure, friendship, and the beauty of nature that \\\\\\\\\\\\\\\"Bambi\\\\\\\\\\\\\\\" represents.\\\\\\\"\\\"},\\\"movie2\\\":{\\\"id\\\":\\\"744\\\",\\\"title\\\":\\\"Top Gun\\\",\\\"plot\\\":\\\"For Lieutenant Pete 'Maverick' Mitchell and his friend and co-pilot Nick 'Goose' Bradshaw, being accepted into an elite training school for fighter pilots is a dream come true. But a tragedy, as well as personal demons, will threaten Pete's dreams of becoming an ace pilot.\\\",\\\"poster_url\\\":\\\"https://image.tmdb.org/t/p/original//xUuHj3CgmZQ9P2cMaqQs4J0d4Zc.jpg\\\",\\\"internal_poster_url\\\":null,\\\"poster_description\\\":\\\"\\\\\\\"The \\\\\\\\\\\\\\\"Top Gun\\\\\\\\\\\\\\\" movie poster features a striking design with two individuals wearing military-style jackets, one of which prominently displays various patches, including a winged emblem and insignias related to aviation and military service. The background showcases the American flag with its recognizable red stripes and white stars, providing a patriotic theme that aligns with the film's focus on elite fighter pilots. The movie\\u2019s title, \\\\\\\\\\\\\\\"Top Gun,\\\\\\\\\\\\\\\" is boldly displayed across the center in large, white capital letters, featuring a stylized white star underneath and flanked by horizontal red stripes, evoking imagery related to aviation and speed. The overall composition conveys themes of action, patriotism, and military aviation.\\\\\\\"\\\"},\\\"genre\\\":\\\"Romance\\\"}}\"","datacontenttype":"text/plain","id":"71250b55-cba5-48ce-ad43-e79680b9242e","pubsubname":"moviepubsub","source":"movie-gallery-svc","specversion":"1.0","time":"2025-10-30T13:32:48Z","topic":"movie-updates","traceid":"00-340f60721cf64225c139f2f4fe2eaa12-ca572e203335be07-01","traceparent":"00-340f60721cf64225c139f2f4fe2eaa12-ca572e203335be07-01","tracestate":"","type":"com.dapr.event.sent"}
    """
    response = await poster_agent.validate_poster_str(data)
    logger.info(response.model_dump_json(indent=2))

if __name__ == "__main__":
    asyncio.run(main())