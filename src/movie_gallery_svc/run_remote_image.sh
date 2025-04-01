#!/bin/bash
# This script builds the docker image for the rambi_event_handler and pushes it to Azure Container Registry
# It also updates the Azure Function App to use the new image
# Usage: ./docker_build.sh
# Ensure you have the Azure CLI installed and logged in
# Ensure you have the Azure Container Registry and Function App created
set -e
if [ -z "$1" ]; then
    PROJECT_DIR="."
else
    PROJECT_DIR=$1
fi

echo "Project Directory: $PROJECT_DIR"

echo -e "\nLoading azd .env file from current environment..."
# Read the environment variables from azd and export them
while IFS= read -r line; do
    # Only process lines with an equal sign
    if [[ "$line" != *"="* ]]; then
        continue
    fi

    key="${line%%=*}"
    value="${line#*=}"
    # Remove leading and trailing quotes if they exist
    value="${value%\"}"
    value="${value#\"}"
    export "$key"="$value"
done < <(azd env get-values)
set -x
remote_tag=azd-deploy-1743419733
az acr login --name ${AZURE_CONTAINER_REGISTRY_ENDPOINT}
IMAGE_TAG=${AZURE_CONTAINER_REGISTRY_ENDPOINT}/azure-rambi/movie_gallery_svc-dev:${remote_tag}
docker pull ${IMAGE_TAG}
docker run -p 5000:5000 ${IMAGE_TAG}
