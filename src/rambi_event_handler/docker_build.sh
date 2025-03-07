set -x
remote_tag=$(openssl rand -hex 4)
az acr login --name azurerambieab45rexk4hhs
IMAGE_NAME=azure-rambi/rambi_event_handler_local
#docker pull azrambiacrb76s6utvi44xo.azurecr.io/azure-rambi/movie_poster_svc:e0d1670d8177b88082771c7b3ad5673b6ea86c5d
docker build -t ${IMAGE_NAME} .
docker tag ${IMAGE_NAME} azurerambieab45rexk4hhs.azurecr.io/azure-rambi/rambi_event_handler_local:${remote_tag}
docker push azurerambieab45rexk4hhs.azurecr.io/azure-rambi/rambi_event_handler_local:${remote_tag}
echo "azurerambieab45rexk4hhs.azurecr.io/azure-rambi/rambi_event_handler_local:${remote_tag}"

az functionapp config container set --image azurerambieab45rexk4hhs.azurecr.io/azure-rambi/rambi_event_handler_local:${remote_tag}  --name rambi-events-handler --resource-group rambi-dev
