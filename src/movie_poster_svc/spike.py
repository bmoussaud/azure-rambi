from azure.storage.blob import BlobServiceClient
from azure.storage.blob._shared.base_client import parse_connection_str
import uuid
import os
import requests
from dotenv import load_dotenv
from main import GenAiMovieService

load_dotenv()
# Your Azure Storage connection string
connection_string = os.getenv("STORAGE_ACCOUNT_CONNECTION_STRING")
print(connection_string)

# Create a BlobServiceClient using the parsed connection string
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client("movieposters")
blob_client = container_client.get_blob_client("spike.png")  
url="https://dalleprodsec.blob.core.windows.net/private/images/2a673a22-10e9-4ec7-bd51-5512c74de608/generated_00.png?se=2025-01-17T16%3A35%3A12Z&sig=kIgPMCCf6P86jlmJ%2FtMBIv6j9Rb1VUj4chydgOxYB1k%3D&ske=2025-01-22T14%3A40%3A06Z&skoid=e52d5ed7-0657-4f62-bc12-7e5dbb260a96&sks=b&skt=2025-01-15T14%3A40%3A06Z&sktid=33e01921-4d64-4f8c-a055-5bdaffd5e33d&skv=2020-10-02&sp=r&spr=https&sr=b&sv=2020-10-02"
print ("uploading.....")
blob_client.upload_blob(requests.get(url,timeout=100).content, overwrite=True, blob_type="BlockBlob")
blob_url = blob_client.url
print(blob_url)
# Verify the client is working by listing containers

GenAiMovieService().generate_poster("a rose elephant")
#GenAiMovieService().store_poster("https://dalleprodsec.blob.core.windows.net/private/images/510f4ba5-f01d-487d-946f-324bce631f3f/generated_00.png?se=2025-01-18T10%3A26%3A59Z&sig=ZSEz8AwKIKUhcMp2Z0jqbBkd5aNvmBWyai9JEYshZVg%3D&ske=2025-01-22T03%3A59%3A33Z&skoid=e52d5ed7-0657-4f62-bc12-7e5dbb260a96&sks=b&skt=2025-01-15T03%3A59%3A33Z&sktid=33e01921-4d64-4f8c-a055-5bdaffd5e33d&skv=2020-10-02&sp=r&spr=https&sr=b&sv=2020-10-02")