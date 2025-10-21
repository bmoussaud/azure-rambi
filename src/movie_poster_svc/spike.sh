#!/bin/bash
set -ex
source .env
title="Cabbage & Chrome Hearts"
plot="In the picturesque countryside, best friends Clara and Tom run a beloved farm known for their signature cabbage dishes. When Emma, a vibrant city artist, visits their farm to find inspiration for her next masterpiece, she and Tom spark an unexpected romance. As Emma immerses herself in rural life, the colorful dynamics between the three friends deepen their bonds and reveal hidden desires. Meanwhile, Clara meets Jamie, a charismatic local craftsman, leading to charming and heartfelt moments. Together, they navigate the blend of rustic charm and vibrant city influences, discovering that love can blossom in the most unexpected places."
poster_description="The poster showcases a vibrant rural landscape with lush green cabbage fields stretching into the distance under a radiant pink and blue sky. In the foreground, a stylish vintage convertible car is parked beside a charming farmhouse, symbolizing the blend of rustic and modern. Two couples are featured: one couple shares a joyful laugh near the car, dressed in fashionable yet casual outfits, while the other couple enjoys a romantic moment under a blossoming tree. Bright and warm colors dominate the scene, with subtle sparkles and soft lighting adding a magical and uplifting feel. The overall aesthetic is lively and heartwarming, capturing the essence of love and friendship in a picturesque setting. Reuse the 2 attached images to find the key symbols and elements to include in the new poster."
ALL="Generate a movie poster based on this description: ${poster_description}. Movie title: ${title}. Movie plot: ${plot}"

echo $AZURE_OPENAI_API_KEY

echo $ALL

curl -X POST "https://azrambidev.cognitiveservices.azure.com/openai/deployments/gpt-image-1/images/edits?api-version=2025-04-01-preview" \
  -H "Authorization: Bearer $AZURE_OPENAI_API_KEY" \
  -F "image[]=@1.jpg" \
  -F "image[]=@2.jpg" \
  -F "prompt=${ALL}" | jq -r '.data[0].b64_json' | base64 --decode > edited_image.png