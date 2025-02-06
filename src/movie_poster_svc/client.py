import redis
import base64
import json
from azure.identity import DefaultAzureCredential
import logging
import sys
from dotenv import load_dotenv
load_dotenv()

scope = "https://redis.azure.com/.default"  # The current scope is for public preview and may change for GA release.
host = "azure-rambi-redis-tfnbpycbnkdum.redis.cache.windows.net"  # Required
port = 6380  # Required

root = logging.getLogger()
root.setLevel(logging.INFO)

# Create a logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Set the logging level to WARNING for the azure.core.pipeline.policies.http_logging_policy logger
logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
logging.getLogger('azure.monitor.opentelemetry.exporter').setLevel(logging.WARNING)

# Set the logging level to WARNING for the urllib3.connectionpool logger
logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)
logger_uvicorn = logging.getLogger('uvicorn.error')
logging.getLogger('azure.identity').setLevel(logging.DEBUG)

scope = "https://redis.azure.com/.default"  # The current scope is for public preview and may change for GA release.
host = "azure-rambi-redis-tfnbpycbnkdum.redis.cache.windows.net"  # Required
port = 6380  # Required
def extract_username_from_token(token):

    """ Extracts the username from the token """
    parts = token.split('.')
    base64_str = parts[1]

    if len(base64_str) % 4 == 2:
        base64_str += "=="
    elif len(base64_str) % 4 == 3:
        base64_str += "="

    json_bytes = base64.b64decode(base64_str)
    json_str = json_bytes.decode('utf-8')
    jwt = json.loads(json_str)

    return jwt['oid']

def connect():
    """ Main function to test the connection to Azure Redis Cache """
    cred = DefaultAzureCredential()
    token = cred.get_token(scope)
    logger.info("Token is: %s", token.token)
    user_name = extract_username_from_token(token.token)
    logger.info("User name is: %s", user_name)
    r = redis.Redis(host=host,
                    port=port,
                    ssl=True,    # ssl connection is required.
                    username=user_name,
                    password=token.token,
                    decode_responses=True)
    logger.info("Connected to Redis...ping")
    r.ping()
    r.set("Az:key1", "value1")
    t = r.get("Az:key1")
    logger.info("Value is: %s", t)
    x = r.get("poster_description:www:https://image.tmdb.org/t/p/original//ywkIu5l3iAgPZvLFEVBDYxLouH8.jpg")
    logger.info("Value is: %s", x)
    logger.info("Value is: %s", type(x))
    logger.info("Value is: %s", x.decode('utf-8'))

if __name__ == '__main__':
    connect()