#!/bin/bash
# Variables
resourceGroup="azrambi"
appName="azrambi-b76s6utvi44xo"
apimName="azure-rambi-apim-b76s6utvi44xo"
subscriptionId="9479b396-5d3e-467a-b89f-ba8400aeb7dd"
myApp="azure-rambi"

# Login to Azure
#az login 
az ad app create --display-name $myApp
echo "create-for-rbac   ${myApp}   ${subscriptionId}   ${resourceGroup}   ${appName}"
az ad sp create-for-rbac --name $myApp --role contributor --scopes "/subscriptions/${subscriptionId}/resourceGroups/${resourceGroup}/providers/Microsoft.Web/sites/${appName}" --json-auth > ${myApp}.json
json_content=$(cat ${myApp}.json)
echo "${json_content}"
echo "create-for-rbac   ${myApp}   ${subscriptionId}   ${resourceGroup}   ${apimName}"
az ad sp create-for-rbac --name $myApp --role contributor --scopes "/subscriptions/${subscriptionId}/resourceGroups/${resourceGroup}/providers/Microsoft.ApiManagement/service/${apimName}" --json-auth > ${myApp}.json
json_content=$(cat ${myApp}.json)
echo "${json_content}"

echo "create-for-rbac   ${myApp}   scope:${subscriptionId}/${resourceGroup}"
az ad sp create-for-rbac --name $myApp --role contributor --scopes "/subscriptions/${subscriptionId}/resourceGroups/${resourceGroup}" --json-auth > ${myApp}.json
json_content=$(cat ${myApp}.json)
echo "${json_content}"

# Set GitHub secrets using the content of the json file
#gh auth login
echo "gh secret set AZURE_CREDENTIALS  -b\"${json_content}\""
gh secret set AZURE_CREDENTIALS  -b"${json_content}"
echo "gh secret set AZURE_SUBSCRIPTION_ID  -b\"${subscriptionId}\""
gh secret set AZURE_SUBSCRIPTION_ID  -b"${subscriptionId}"
rm ${myApp}.json
