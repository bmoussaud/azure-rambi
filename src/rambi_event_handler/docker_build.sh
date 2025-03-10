set -x
remote_tag=$(openssl rand -hex 4)
az acr login --name azurerambiv4xifqo5xvenu
IMAGE_NAME=azure-rambi/rambi_event_handler_local
#docker pull azrambiacrb76s6utvi44xo.azurecr.io/azure-rambi/movie_poster_svc:e0d1670d8177b88082771c7b3ad5673b6ea86c5d
docker build -t ${IMAGE_NAME} .
docker tag ${IMAGE_NAME} azurerambiv4xifqo5xvenu.azurecr.io/azure-rambi/rambi_event_handler_local:${remote_tag}
docker push azurerambiv4xifqo5xvenu.azurecr.io/azure-rambi/rambi_event_handler_local:${remote_tag}
echo "azurerambiv4xifqo5xvenu.azurecr.io/azure-rambi/rambi_event_handler_local:${remote_tag}"

az functionapp config container set --image azurerambiv4xifqo5xvenu.azurecr.io/azure-rambi/rambi_event_handler_local:${remote_tag}  --name rambi-events-handler --resource-group azrambi-dev
