import json

# Load the JSON file
with open('src/apim/definition/tmdb_v3.json', 'r') as file:
    data = json.load(file)

# Extract the operation '/3/search/movie'
operation = data.get('paths', {}).get('/3/search/movie', {})

# Pretty-print the extracted operation
print(json.dumps(operation, indent=2))