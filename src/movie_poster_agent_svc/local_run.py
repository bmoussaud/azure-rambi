from main import PosterValidationAgent, PosterValidationRequest, PosterValidationResponse, poster_agent
import httpx
import asyncio  

async def main():
    request = PosterValidationRequest(
        poster_url="https://gui-svc.niceriver-71d47c14.francecentral.azurecontainerapps.io/poster/525_18450_Romance_59399.png",
        poster_description="The poster features a charming couple dressed in stylish attire, blending classic black suits with vibrant accessories. The man wears a playful mask, hinting at his secret identity, while the woman holds a paintbrush, symbolizing her artistic nature. They stand back-to-back against a backdrop of soft blue hues, evoking a romantic and musical atmosphere. Surrounding them are subtle illustrations of musical notes and artistic elements, showcasing their creative passions. The composition emphasizes their connection and partnership, capturing the essence of love and collaboration central to the film's theme.",
        movie_title="Zorro & The Heartstrings",
        movie_genre="Romance"
    )
    request = PosterValidationRequest(
        poster_url="https://nazrambihxklazmdpap4s.blob.core.windows.net/movieposters/525_3170_Romance_87490.png",
        poster_description="The poster showcases two charismatic mice dressed in stylish outfits—one in a sharp black suit with a white shirt and a trendy hat, and the other in a colorful blazer with a playful tie. They both wear cool sunglasses, exuding confidence and charm. Behind them is a vibrant, gradient background transitioning from light blue at the top to deep blue at the bottom, adding a lively and dynamic feel. Surrounding the main characters are their diverse band members, each holding different musical instruments that hint at a fun and energetic performance. The scene is set against a backdrop of a bustling animated cityscape with musical notes floating around, emphasizing the film's focus on music and camaraderie. The overall aesthetic is bright, engaging, and full of movement, capturing the essence of an uplifting animated musical adventure.",
        movie_title="The Melody Mice",
        movie_genre="Animation",
        language="French"
    )
    response = await poster_agent.validate_poster(request=request)
    #print(response)
    import json
    print(response.model_dump_json(indent=2))

if __name__ == "__main__":
    asyncio.run(main())