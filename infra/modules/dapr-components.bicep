@description('Primary location for all resources')
param location string

@description('The name of the container apps environment.')
param containerAppsEnvironmentName string

@description('Azure Managed Identity name')
param azureRambiAppsManagedIdentityName string

@description('Cosmos DB account document endpoint')
param cosmosDbAccountDocumentEndpoint string

@description('Service Bus namespace name')
param serviceBusNamespaceName string

@description('Storage account name.')
param storageAccountName string

resource azrAppsMi 'Microsoft.ManagedIdentity/userAssignedIdentities@2022-01-31-preview' existing = {
  name: azureRambiAppsManagedIdentityName
}

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2022-03-01' existing = {
  name: containerAppsEnvironmentName
}

resource movieGalleryStatestoreComponent 'Microsoft.App/managedEnvironments/daprComponents@2025-01-01' = {
  parent: containerAppsEnvironment
  name: 'movie-gallery-svc-statetore'

  properties: {
    componentType: 'state.azure.cosmosdb'
    version: 'v1'
    initTimeout: '5m'
    secrets: []
    metadata: [
      {
        name: 'url'
        value: cosmosDbAccountDocumentEndpoint
      }
      {
        name: 'database'
        value: 'azrambi-db'
      }
      {
        name: 'collection'
        value: 'movies'
      }
      {
        name: 'azureClientId'
        value: azrAppsMi.properties.clientId
      }
    ]
    scopes: [
      'movie-gallery-svc'
    ]
  }
}

resource moviePosterAgentStatestoreComponent 'Microsoft.App/managedEnvironments/daprComponents@2025-01-01' = {
  parent: containerAppsEnvironment
  name: 'movie-poster-agent-svc-statetore'

  properties: {
    componentType: 'state.azure.cosmosdb'
    version: 'v1'
    initTimeout: '5m'
    secrets: []
    metadata: [
      {
        name: 'url'
        value: cosmosDbAccountDocumentEndpoint
      }
      {
        name: 'database'
        value: 'azrambi-db'
      }
      {
        name: 'collection'
        value: 'validations'
      }
      {
        name: 'azureClientId'
        value: azrAppsMi.properties.clientId
      }
    ]
    scopes: [
      'movie-poster-agent-svc'
    ]
  }
}

resource pubsubComponent 'Microsoft.App/managedEnvironments/daprComponents@2025-01-01' = {
  parent: containerAppsEnvironment
  name: 'moviepubsub'
  properties: {
    componentType: 'pubsub.azure.servicebus'
    version: 'v1'
    metadata: [
      {
        name: 'namespaceName'
        value: '${serviceBusNamespaceName}.servicebus.windows.net'
      }
      {
        name: 'azureClientId'
        value: azrAppsMi.properties.clientId
      }
    ]

    scopes: [
      'movie-gallery-svc'
      'movie-poster-agent-svc'
    ]
  }
}

resource queueComponent 'Microsoft.App/managedEnvironments/daprComponents@2025-01-01' = {
  parent: containerAppsEnvironment
  name: 'movieposters-events-queue'
  properties: {
    componentType: 'bindings.azure.storagequeues'
    version: 'v1'
    initTimeout: '5m'
    secrets: []
    metadata: [
      {
        name: 'storageAccount'
        value: storageAccountName
      }
      {
        name: 'queue'
        value: 'movieposters-events'
      }
      {
        name: 'azureClientId'
        value: azrAppsMi.properties.clientId
      }
    ]
    scopes: [
      'movie-gallery-svc'
    ]
  }
}
