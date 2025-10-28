#!/bin/bash
set -ex
source .env

MOVIE_ID="1369_3170_Family_59954"


curl -X GET "$MOVIE_GALLERY_ENDPOINT/movies/$MOVIE_ID" | jq .
movie_title=$(curl -X GET "$MOVIE_GALLERY_ENDPOINT/movies/$MOVIE_ID" | jq .title)
echo "Movie title: $movie_title"
poster_description=$(curl -X GET "$MOVIE_GALLERY_ENDPOINT/movies/$MOVIE_ID" | jq .poster_description)
echo "Poster description: $poster_description"
poster_url=$(curl -X GET "$MOVIE_GALLERY_ENDPOINT/movies/$MOVIE_ID" | jq .poster_url | tr -d '"')
echo "Poster URL: $poster_url"
genre=$(curl -X GET "$MOVIE_GALLERY_ENDPOINT/movies/$MOVIE_ID" | jq .payload.genre  )
echo "Genre: $genre"


curl -X POST "$MOVIE_POSTER_AGENT_ENDPOINT/validate" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "poster_description=${poster_description}" \
  -d "poster_url=${STORAGE_ACCOUNT_BLOB_URL}movieposters/${MOVIE_ID}.png" \
  -d "movie_title=${movie_title}" \
  -d "movie_genre=${genre}" \
  -d "language=french" | jq .