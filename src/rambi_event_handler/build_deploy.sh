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
remote_tag=$(openssl rand -hex 4)
az acr login --name ${AZURE_CONTAINER_REGISTRY_ENDPOINT}
IMAGE_NAME=azure-rambi/rambi_event_handler_local
#docker pull azrambiacrb76s6utvi44xo.azurecr.io/azure-rambi/movie_poster_svc:e0d1670d8177b88082771c7b3ad5673b6ea86c5d
#cd $PROJECT_DIR  && az acr build --registry ${AZURE_CONTAINER_REGISTRY_ENDPOINT} --image ${IMAGE_NAME}:${remote_tag} -f Dockerfile . 
#exit 1
cd ${PROJECT_DIR} 
docker build -t ${IMAGE_NAME} .
docker tag ${IMAGE_NAME} ${AZURE_CONTAINER_REGISTRY_ENDPOINT}/azure-rambi/rambi_event_handler_local:${remote_tag}
docker push ${AZURE_CONTAINER_REGISTRY_ENDPOINT}/azure-rambi/rambi_event_handler_local:${remote_tag}
echo "${AZURE_CONTAINER_REGISTRY_ENDPOINT}/azure-rambi/rambi_event_handler_local:${remote_tag}"
azd env set RAMBI_EVENT_HANDLER_IMAGE "${AZURE_CONTAINER_REGISTRY_ENDPOINT}/azure-rambi/rambi_event_handler_local:${remote_tag}"
az functionapp config container set --image ${AZURE_CONTAINER_REGISTRY_ENDPOINT}/azure-rambi/rambi_event_handler_local:${remote_tag}  --name rambi-events-handler --resource-group ${AZURE_RESOURCE_GROUP}