# test_blob_upload.py
import os
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
load_dotenv()
# Set these environment variables or replace with your values
STORAGE_ACCOUNT_URL = os.getenv("STORAGE_ACCOUNT_BLOB_URL")
CONTAINER_NAME = "movieposters"
BLOB_NAME = "test_upload.txt"
CONTENT = b"Hello from local test!"



def main():
    # Authenticate using DefaultAzureCredential (works with az login/azd login)
    print("STORAGE_ACCOUNT_BLOB_URL=", STORAGE_ACCOUNT_URL)
    credential = DefaultAzureCredential()
    token = credential.get_token("https://storage.azure.com/.default")
    print(token.token)
    blob_service_client = BlobServiceClient(account_url=STORAGE_ACCOUNT_URL, credential=credential)
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)
    blob_client = container_client.get_blob_client(BLOB_NAME)
    blob_client.upload_blob(CONTENT, overwrite=True)
    print(f"Uploaded {BLOB_NAME} to {CONTAINER_NAME}")

if __name__ == "__main__":
    main()