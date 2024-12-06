#!/bin/bash
set -x
# Define the API endpoint and the header
API_URL="https://azure-rambi-apim-b76s6utvi44xo.azure-api.net/tmdb/3/search/movie?query=bambi"
HEADER="Ocp-Apim-Subscription-Key: 457a8296b79045c4a0adda71cfc9a0ec"

# Make the GET request using curl
curl -H "$HEADER" -X GET "$API_URL"