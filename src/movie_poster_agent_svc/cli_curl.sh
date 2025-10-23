#!/bin/bash
set -ex

curl -X POST "http://localhost:8005/validate" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "poster_description=The poster showcases two charismatic mice dressed in stylish outfits—one in a sharp black suit with a white shirt and a trendy hat, and the other in a colorful blazer with a playful tie. They both wear cool sunglasses, exuding confidence and charm. Behind them is a vibrant, gradient background transitioning from light blue at the top to deep blue at the bottom, adding a lively and dynamic feel. Surrounding the main characters are their diverse band members, each holding different musical instruments that hint at a fun and energetic performance. The scene is set against a backdrop of a bustling animated cityscape with musical notes floating around, emphasizing the film's focus on music and camaraderie. The overall aesthetic is bright, engaging, and full of movement, capturing the essence of an uplifting animated musical adventure." \
  -d "poster_url=https://gui-svc.niceriver-71d47c14.francecentral.azurecontainerapps.io/poster/525_420821_Animation_66602.png" \
  -d "movie_title=The Melody Mice" \
  -d "movie_genre=Anime" \
  -d "language=french" | jq .