#!/bin/bash
set -x 
resourceGroup="azrambi"
appName="azrambi-b76s6utvi44xo"
subscriptionId="9479b396-5d3e-467a-b89f-ba8400aeb7dd"
myApp="azure-rambi"

az webapp config set --resource-group ${resourceGroup} -n ${appName} --remote-debugging-enabled=false
az webapp create-remote-connection --subscription ${subscriptionId} --resource-group ${resourceGroup} -n ${appName} 
