#!/bin/bash
# Variables
source $1
resourceGroup=${AZURE_RESOURCE_GROUP}
subscriptionId=${AZURE_SUBSCRIPTION_ID}

myApp="azure-rambi-${AZURE_ENV_NAME}"
echo "create-for-rbac   ${myApp}   ${subscriptionId}   ${resourceGroup}   "

# Login to Azure
#az login 
az ad app create --display-name $myApp


echo "create-for-rbac   ${myApp}   scope:${subscriptionId}/${resourceGroup}"
az ad sp create-for-rbac --name $myApp --role Owner --scopes "/subscriptions/${subscriptionId}/resourceGroups/${resourceGroup}" --json-auth > ${myApp}.json
json_content=$(cat ${myApp}.json)
echo "${json_content}"

service_princial=$(echo "${json_content}" | jq -r '.clientId')
service_principal_password=$(echo "${json_content}" | jq -r '.clientSecret')
tenant=$(echo "${json_content}" | jq -r '.tenantId')
clientId=$(echo "${json_content}" | jq -r '.clientId')

echo "------"
echo "${service_princial}/${service_principal_password}/${tenant}"
echo "------"

cat <<EOF > .env
AZURE_SERVICE_PRINCIPAL_ID=${service_princial}
AZURE_SERVICE_PRINCIPAL_PASSWORD=${service_principal_password}
AZURE_TENANT_ID=${tenant}
AZURE_SUBSCRIPTION_ID=${subscriptionId}
EOF
 
cat .env

# Set GitHub secrets using the content of the json file
#gh auth login
echo "gh secret set AZURE_CREDENTIALS  -b\"${json_content}\""
gh secret set AZURE_CREDENTIALS  -b"${json_content}"
set -x 
gh secret set -f .env   

gh variable set AZURE_RESOURCE_GROUP -b"${resourceGroup}"
gh variable set AZURE_ENV_NAME -b"${AZURE_ENV_NAME}"
gh variable set AZURE_SUBSCRIPTION_ID -b"${subscriptionId}"
gh variable set AZURE_LOCATION -b"${AZURE_LOCATION}"
gh variable set AZURE_TENANT_ID -b"${tenant}"
gh variable set AZURE_CLIENT_ID -b"${clientId}"

rm ${myApp}.json
rm .env