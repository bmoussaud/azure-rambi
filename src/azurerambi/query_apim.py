# This code is an example of how to use the OpenAI API with Azure API Management (APIM) in a Jupyter Notebook.
import requests
import json
import os
import logging
from dotenv import load_dotenv
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

load_dotenv()

def query():
    """Query the OpenAI API using Azure API Management."""
    print("Querying the OpenAI API using Azure API Management")
    # Set the parameters
    apim_url = "azure-rambi-apim-tfnbpycbnkdum.azure-api.net/azure-openai"
    deployment_name = "gpt-4o"
    api_version = "2024-08-01-preview"
    subscription_key = os.getenv("APIM_SUBSCRIPTION_KEY")
    # Construct the URL and headers
    url = f"https://{apim_url}/openai/deployments/{deployment_name}/chat/completions?api-version={api_version}"
    print(url)
    #url="https://azrambi-openai-tfnbpycbnkdum.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview"
    headers = {
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Key": subscription_key,
        "api-key": subscription_key
    }

    # Define the JSON payload
    json_payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are an AI assistant that helps people find information."
            },
            {
                "role": "user",
                "content": "What are the differences between Azure Machine Learning and Azure AI services?"
            }
        ],
        "temperature": 0.7,
        "top_p": 0.95,
        "max_tokens": 800
    }

    # Make the POST request
    response = requests.post(url, headers=headers, json=json_payload)

    # Print the response text (or you can process it further as needed)
    print(response.text)


for _ in range(10):
    query()
    time.sleep(2)