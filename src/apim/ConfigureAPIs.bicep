var apiManagementServiceName = 'azure-rambi-apim-${uniqueString(resourceGroup().id)}'

module tmdbApi 'modules/api.bicep' = {
  name: 'apiTMDB'
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
  dependsOn: [
    tmdbApiKey
  ]
}

module tmdbApiKey 'modules/nv.bicep' ={
  name: 'tmdbApiKey'
  params: {
    apimName: apiManagementServiceName
    keyName: 'tmdb-api-key'
    displayName: 'TMDB API Key'
    value: '68d40b1b40c8ba0c137374cf5dc3e7a1'
  }
  
}




