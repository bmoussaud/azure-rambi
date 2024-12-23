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

var openAIName = 'azrambi-openai-${uniqueString(resourceGroup().id)}'
resource openAI 'Microsoft.CognitiveServices/accounts@2023-05-01' existing = {
  name: openAIName
}

module openaiApi 'modules/api.bicep' = {
  name: 'apiOpenAI'
  params: {
    apimName: apiManagementServiceName
    apiName: 'OpenAI'
    apiPath: '/azure-openai/openai'
    openApiJson: 'https://raw.githubusercontent.com/bmoussaud/azure-rambi/refs/heads/main/src/apim/definition/azure_open_ai.json'
    openApiXml: 'https://raw.githubusercontent.com/bmoussaud/azure-rambi/refs/heads/main/src/apim/policies/azure_open_ai.xml'
    serviceUrlPrimary: '${openAI.properties.endpoint}/openai'
    apiSubscriptionName: 'azure-rambi-sub'
    aiLoggerName: 'aiLogger'
  }
}

var containerMoviePosterSvcName = 'movie-poster-svc-${uniqueString(resourceGroup().id)}'
resource containerMoviePosterSvcApp 'Microsoft.App/containerApps@2024-10-02-preview' existing = {
  name: containerMoviePosterSvcName
}
module moviePoster 'modules/api.bicep' = {
  name: 'moviePoster'
  params: {
    apimName: apiManagementServiceName
    apiName: 'moviePoster'
    apiPath: '/movie_poster'
    openApiJson: 'https://raw.githubusercontent.com/bmoussaud/azure-rambi/refs/heads/main/src/apim/definition/movie_poster.json'
    openApiXml: 'https://raw.githubusercontent.com/bmoussaud/azure-rambi/refs/heads/main/src/apim/policies/movie_poster.xml'
    serviceUrlPrimary: 'https://${containerMoviePosterSvcApp.properties.configuration.ingress.fqdn}'
    apiSubscriptionName: 'azure-rambi-sub'
    aiLoggerName: 'aiLogger'
  }
}
