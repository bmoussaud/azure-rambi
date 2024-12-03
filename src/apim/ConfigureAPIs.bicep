@description('Name of the resource group')
param resourceGroupName string = resourceGroup().name

var apiManagementServiceName = 'azure-rambi-apim-${uniqueString(resourceGroup().id)}'

module api 'modules/api.bicep' = {
  name: 'apiTMDB'
  scope: resourceGroup(resourceGroupName)
  params: {
    apimName: apiManagementServiceName
    apiName: 'TMDB'
    apiPath: '/tmdb'
    openApiJson : 'https://raw.githubusercontent.com/bmoussaud/azure-rambi/refs/heads/main/src/apim/definition/tmdb_search_movie.json'
    openApiXml : 'https://raw.githubusercontent.com/bmoussaud/azure-rambi/refs/heads/main/src/apim/policies/tmdb.xml'
    serviceUrlPrimary : 'https://api.themoviedb.org'
    apiSubscriptionName: 'azure-rambi-sub'
    aiLoggerId: 'diag_apiManagement.outputs.aiLoggerId'
  }

}



