var apiManagementServiceName = 'azure-rambi-apim-${uniqueString(resourceGroup().id)}'

module tmdbApi 'modules/api.bicep' = {
  name: 'apiTMDB'
  params: {
    apimName: apiManagementServiceName
    apiName: 'TMDB'
    apiPath: '/tmdb'
    openApiJson: loadTextContent('definition/tmdb_search_movie.json')
    openApiXml: loadTextContent('policies/tmdb.xml')
    serviceUrlPrimary: 'https://api.themoviedb.org'
    apiSubscriptionName: 'azure-rambi-sub'
    aiLoggerId: 'diag_apiManagement.outputs.aiLoggerId'
  }
  dependsOn: [
    tmdbApiKey
  ]
}

module tmdbApiKey 'modules/nv.bicep' = {
  name: 'tmdbApiKey'
  params: {
    apimName: apiManagementServiceName
    keyName: 'tmdb-api-key'
    value: 'your-api-key-here'
  }
}




