# This code is an example of how to use the OpenAI API with Azure API Management (APIM) in a Jupyter Notebook.
import requests
import json
import os
import logging
from dotenv import load_dotenv
import time
import random
import openai
from openai import AzureOpenAI
from pydantic import BaseModel
from opentelemetry.instrumentation.openai import OpenAIInstrumentor
from azure.ai.inference.tracing import AIInferenceInstrumentor 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

load_dotenv()
OpenAIInstrumentor().instrument()
AIInferenceInstrumentor().instrument() 

def query():
    """Query the OpenAI API using Azure API Management."""
    print("Querying the OpenAI API using Azure API Management")
    
    subscription_key = "c6e983f9b12b43a3b98995d8956f0079"
    
    # Define the JSON payload
    messages=[
            {
                "role": "user",
                "content": "You are an AI assistant that helps people find information."
            },
            {
                "role": "user",
                "content": "What are the differences between Azure Machine Learning and Azure AI services?"
            }
        ]
    
    client = AzureOpenAI(
            api_key=subscription_key,
            api_version="2024-08-01-preview",
            azure_endpoint="https://azure-rambi-apim-tfnbpycbnkdum.azure-api.net/azure-openai"
        )
    #print(json.dumps(json_payload, indent=2))

    o1_response = client.chat.completions.create(model="gpt-5-mini", messages=messages)
    o1_response_content = o1_response.choices[0].message.content
    print(o1_response_content)
    print("---")

    completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=messages)
    time.sleep(1)
    message = completion.choices[0].message
    print(message)
    print("---")


for _ in range(10):
    query()
    time.sleep(2)