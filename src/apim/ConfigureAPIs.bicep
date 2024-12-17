var apiManagementServiceName = 'azure-rambi-apim-${uniqueString(resourceGroup().id)}'

module tmdbApi 'modules/api.bicep' = {
  name: 'apiTMDB'
  params: {
    apimName: apiManagementServiceName
    apiName: 'TMDB'
    apiPath: '/tmdb'
    openApiJson: 'https://raw.githubusercontent.com/bmoussaud/azure-rambi/refs/heads/main/src/apim/definition/tmdb_search_movie.json'
    openApiXml: 'https://raw.githubusercontent.com/bmoussaud/azure-rambi/refs/heads/main/src/apim/policies/tmdb.xml'
    serviceUrlPrimary: 'https://api.themoviedb.org'
    apiSubscriptionName: 'azure-rambi-sub'
    aiLoggerName: 'aiLogger'
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
    value: 'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI2OGQ0MGIxYjQwYzhiYTBjMTM3Mzc0Y2Y1ZGMzZTdhMSIsIm5iZiI6MTcxMzI1NDA2Mi43MjgsInN1YiI6IjY2MWUyZWFlZDE4ZmI5MDE3ZGNhNjcxMSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.LNNv4AbXo8asYhfL3Pjr9S-EOIe-Chu1iKSr-gRfmo4'
  }
}

module openaiApi 'modules/api.bicep' = {
  name: 'apiOpenAI'
  params: {
    apimName: apiManagementServiceName
    apiName: 'OpenAI'
    apiPath: '/azure-rambi/openai'
    openApiJson: 'https://raw.githubusercontent.com/bmoussaud/azure-rambi/refs/heads/main/src/apim/definition/azure_open_ai.json'
    openApiXml: 'https://raw.githubusercontent.com/bmoussaud/azure-rambi/refs/heads/main/src/apim/policies/azure_open_ai.xml'
    serviceUrlPrimary: 'https://azrambi-openai-b76s6utvi44xo.openai.azure.com/openai'
    apiSubscriptionName: 'azure-rambi-sub'
    aiLoggerName: 'aiLogger'
  }
}
