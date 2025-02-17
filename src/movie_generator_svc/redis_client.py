import os
import redis
import logging    
import base64
import json
from azure.identity import ManagedIdentityCredential

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class RedisClient:
    """RedisClient class"""
    def __init__(self):
        logger.info("Initializing Redis client")
        #use managed identity to connect to redis (azure-rambi-storage-contributor)
        managed_id_credential = ManagedIdentityCredential(client_id=os.getenv("AZURE_CLIENT_ID"))
        logger.info("managedIdCredential: %s", managed_id_credential)
        redis_scope = "https://redis.azure.com/.default"
        logger.info("Redis Scope: %s", redis_scope)
        token = managed_id_credential.get_token(redis_scope)
        logger.info("Token: %s", token)
        if token is None:
            logger.error("Redis client using password")
            self.redis_client = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), password=os.getenv("REDIS_PASSWORD"),ssl=True )
        else:
            logger.info("Redis Client using token")
            user_name = self.extract_username_from_token(token.token)
            logger.info("User name: %s", user_name)
            self.redis_client = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), username=user_name, password=token.token,ssl=True,decode_responses=True)
        logger.info("Redis ping: %s", self.redis_client.ping())
        self._timeout = os.getenv("REDIS_KEY_TIMEOUT", 600)  # Default timeout is 600 seconds (10 mn)
        logger.info("Setting key timeout: %s seconds", self._timeout)

    def extract_username_from_token(self,token):
        """Extract the username from the token"""
        parts = token.split('.')
        base64_str = parts[1]

        if len(base64_str) % 4 == 2:
            base64_str += "=="
        elif len(base64_str) % 4 == 3:
            base64_str += "="

        json_bytes = base64.b64decode(base64_str)
        json_str = json_bytes.decode('utf-8')
        jwt = json.loads(json_str)
        logger.info("extract_username_from_token: %s", jwt)
        logger.info("extract_username_from_token oid: %s", jwt['oid'])
        return jwt['oid']

    def get(self, key):
        """Get the value of a key."""
        logger.info("Getting key: %s", key)
        return self.redis_client.get(key)

    def set(self, key, value):
        """Set the value of a key."""
        logger.info("Setting key: %s", key)
        # Set a timeout for the key
        self.redis_client.setex(key, self._timeout, value)
        return value