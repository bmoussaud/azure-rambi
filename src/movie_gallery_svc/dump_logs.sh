#!/bin/bash
# This script dumps the logs from the movie_gallery_svc container app
# Usage: ./dump_logs.sh
# Ensure you have the Azure CLI installed and logged in
set -ex
CONTAINERAPPS_ENVIRONMENT="azure-rambi"
RESOURCE_GROUP="rg-dev-rambi"
LOG_ANALYTICS_WORKSPACE_CLIENT_ID=$(az containerapp env show --name $CONTAINERAPPS_ENVIRONMENT --resource-group $RESOURCE_GROUP --query properties.appLogsConfiguration.logAnalyticsConfiguration.customerId --out tsv)
 az monitor log-analytics query   --workspace $LOG_ANALYTICS_WORKSPACE_CLIENT_ID \
  --analytics-query "ContainerAppConsoleLogs_CL | where ContainerAppName_s == 'movie-gallery-svc'  | project ContainerAppName_s, Log_s, TimeGenerated | sort by TimeGenerated | take  20" \
  --out table
