@minLength(1)
@description('Primary location for all resources')
param location string

@description('Restore the service instead of creating a new instance. This is useful if you previously soft-deleted the service and want to restore it. If you are restoring a service, set this to true. Otherwise, leave this as false.')
param restore bool = false

var openAIName = 'azrambi-openai-${uniqueString(resourceGroup().id)}'
var acrName = 'azurerambi${uniqueString(resourceGroup().id)}'

@description('Model deployments for OpenAI')
param deployments array = [
  {
    name: 'gpt-4o'
    capacity: 40
    version: '2024-08-06' //2024-08-06 ?
    deployment: 'Standard'
  }
  {
    name: 'dall-e-3'
    model: 'dall-e-3'
    version: '3.0'
    capacity: 1
    deployment: 'Standard'
  }
  {
    name: 'o1-mini'
    model: 'o1-mini'
    version: '2024-09-12'
    capacity: 10
    deployment: 'GlobalStandard'
  }
]

@description('Creates an Azure OpenAI resource.')
resource openAI 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: openAIName
  location: 'Sweden Central'
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: openAIName
    publicNetworkAccess: 'Enabled'
    restore: restore
  }
}

@batchSize(1)
resource deployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = [
  for deployment in deployments: {
    parent: openAI
    name: deployment.name
    sku: {
      name: deployment.deployment
      capacity: deployment.capacity
    }
    properties: {
      model: {
        format: 'OpenAI'
        name: deployment.name
        version: deployment.version
      }
    }
  }
]

@description('Creates an Azure Key Vault.')
resource kv 'Microsoft.KeyVault/vaults@2024-04-01-preview' = {
  name: 'rambikv${uniqueString(resourceGroup().id)}'
  location: location
  properties: {
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    sku: {
      name: 'standard'
      family: 'A'
    }
    //publicNetworkAccess: 'Enabled'
  }
}
resource azrKeyVaultContributor 'Microsoft.ManagedIdentity/userAssignedIdentities@2018-11-30' = {
  name: 'azure-rambi-keyvault-user'
  location: location
}

// Assign the Key Vault Secrets Officer role to the managed identity
resource keyVaultContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid(kv.id, azrKeyVaultContributor.id, 'Key Vault Contributor Role')
  scope: kv
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '4633458b-17de-408a-b874-0445c86b69e6' // Key Vault Secrets Officer
    )
    principalId: azrKeyVaultContributor.properties.principalId
  }
}

@description('This is the built-in Key Vault Secrets Officer role. See https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/security#key-vault-secrets-user')
resource keyVaultSecretsUserRoleDefinition 'Microsoft.Authorization/roleDefinitions@2018-01-01-preview' existing = {
  scope: subscription()
  name: '4633458b-17de-408a-b874-0445c86b69e6'
}

//Key Value Secret User
@description('Assigns the API Management service the role to browse and read the keys of the Key Vault to the APIM')
resource keyVaultSecretUserRoleAssignment 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid(kv.id, 'ApiManagement', keyVaultSecretsUserRoleDefinition.id)
  scope: kv
  properties: {
    roleDefinitionId: keyVaultSecretsUserRoleDefinition.id
    principalId: apiManagement.outputs.apiManagementIdentityPrincipalId
  }
}

// add secrets to the key vault
resource secretAzureOpenAIEndPoint 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  parent: kv
  name: 'AZURE-OPENAI-ENDPOINT'
  properties: {
    value: 'https://${apiManagement.outputs.apiManagementProxyHostName}/azure-openai'
  }
}

@description('Creates an Azure Key Vault Secret API-SUBSCRIPTION-KEY.')
resource secretApimSubKey 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  parent: kv
  name: 'APIM-SUBSCRIPTIONKEY'
  properties: {
    value: apiManagement.outputs.apiAdminSubscriptionKey
  }
}
@description('Creates an Azure Key Vault Secret APPINSIGHTH-INSTRUMENTATIONKEY.')
resource secretAppInsightInstKey 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  parent: kv
  name: 'APPINSIGHTS-INSTRUMENTATIONKEY'
  properties: {
    value: applicationInsights.outputs.instrumentationKey
  }
}
@description('Creates an Azure Key Vault Secret APPLICATIONINSIGHTS-CONNECTION-STRING.')
resource secretAppInsightCS 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  parent: kv
  name: 'APPLICATIONINSIGHTS-CONNECTIONSTRING'
  properties: {
    value: applicationInsights.outputs.connectionString
  }
}
@description('Creates an Azure Key Vault Secret APIM-ENDPOINT.')
resource secretApimEndpoint 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  parent: kv
  name: 'APIM-ENDPOINT'
  properties: {
    value: apiManagement.outputs.apiManagementProxyHostName
  }
}

//Cognitive Services OpenAI User
resource cognitiveServiceOpenAIUserRoleAssignment 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid('Cognitive Services OpenAI User Role On API Management')
  scope: openAI
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd' // Cognitive Services OpenAI User
    )
    principalId: apiManagement.outputs.apiManagementIdentityPrincipalId
  }
}

module apiManagement 'modules/api-management.bicep' = {
  name: 'api-management'
  params: {
    location: location
    serviceName: 'azrambi-apim-${uniqueString(resourceGroup().id)}'
    publisherName: 'Azure Rambi Suites'
    publisherEmail: 'azure-rambi@contososuites.com'
    skuName: 'Basicv2'
    skuCount: 1
    aiName: 'azure-rambi-app-insights'
    //eventHubNamespaceName: 'azure-rambi-ehn-${uniqueString(resourceGroup().id)}'
    //eventHubName: 'azure-rambi-eh-${uniqueString(resourceGroup().id)}'
  }
  dependsOn: [
    logAnalyticsWorkspace
    eventHub
    applicationInsights
  ]
}

module tmdbApi 'modules/api.bicep' = {
  name: 'apiTMDB'
  params: {
    apimName: apiManagement.outputs.name
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

// add TMBD Apike secrets to the key vault
resource secretTMDBApiKey 'Microsoft.KeyVault/vaults/secrets@2024-04-01-preview' = {
  parent: kv
  name: 'TMDB-API-KEY'
  properties: {
    value: 'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI2OGQ0MGIxYjQwYzhiYTBjMTM3Mzc0Y2Y1ZGMzZTdhMSIsIm5iZiI6MTcxMzI1NDA2Mi43MjgsInN1YiI6IjY2MWUyZWFlZDE4ZmI5MDE3ZGNhNjcxMSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.LNNv4AbXo8asYhfL3Pjr9S-EOIe-Chu1iKSr-gRfmo4'
  }
}

module tmdbApiKey 'modules/nvkv.bicep' = {
  name: 'tmdbApiKey'
  params: {
    apimName: apiManagement.outputs.name
    keyName: 'tmdb-api-key'
    keyVaultName: kv.name
    secretName: secretTMDBApiKey.name
  }
  dependsOn: [
    keyVaultSecretUserRoleAssignment //this role assignment is needed to allow the API Management service to access the Key Vault
  ]
}

module openaiApi 'modules/api.bicep' = {
  name: 'apiOpenAI'
  params: {
    apimName: apiManagement.outputs.name
    apiName: 'OpenAI'
    apiPath: '/azure-openai/openai'
    openApiJson: 'https://raw.githubusercontent.com/bmoussaud/azure-rambi/refs/heads/main/src/apim/definition/azure_open_ai.json'
    openApiXml: 'https://raw.githubusercontent.com/bmoussaud/azure-rambi/refs/heads/main/src/apim/policies/azure_open_ai.xml'
    serviceUrlPrimary: '${openAI.properties.endpoint}/openai'
    apiSubscriptionName: 'azure-rambi-sub'
    aiLoggerName: 'aiLogger'
  }
}

module logAnalyticsWorkspace 'modules/log-analytics-workspace.bicep' = {
  name: 'log-analytics-workspace'
  params: {
    location: location
    logAnalyticsName: 'azure-rambi-log-analytics'
  }
}

module eventHub 'modules/event-hub.bicep' = {
  name: 'event-hub'
  params: {
    location: location
    eventHubNamespaceName: 'azure-rambi-ehn-${uniqueString(resourceGroup().id)}'
    eventHubName: 'azure-rambi-eh-${uniqueString(resourceGroup().id)}'
  }
}

module applicationInsights 'modules/app-insights.bicep' = {
  name: 'application-insights'
  params: {
    location: location
    workspaceName: logAnalyticsWorkspace.outputs.name
    applicationInsightsName: 'azure-rambi-app-insights'
  }
}

module redis 'modules/redis.bicep' = {
  name: 'redis-cache'
  params: {
    location: location
    redisCacheName: 'azure-rambi-redis-${uniqueString(resourceGroup().id)}'
    redisContributorName: azrStorageContributor.name
  }
}

@description('Creates an Azure Container Registry.')
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: acrName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
  tags: {
    displayName: 'Container Registry'
    'container.registry': acrName
  }
}

@description('Creates an Azure Container Apps Environment.')
resource containerAppsEnv 'Microsoft.App/managedEnvironments@2024-10-02-preview' = {
  name: 'azure-rambi'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${azrKeyVaultContributor.id}': {}
    }
  }

  properties: {
    daprAIInstrumentationKey: applicationInsights.outputs.instrumentationKey

    appInsightsConfiguration: {
      connectionString: applicationInsights.outputs.connectionString
    }
    openTelemetryConfiguration: {
      tracesConfiguration: {
        destinations: ['appInsights']
      }
      logsConfiguration: {
        destinations: ['appInsights']
      }
    }
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.outputs.customerId
        sharedKey: logAnalyticsWorkspace.outputs.primarySharedKey
      }
    }

    workloadProfiles: [
      {
        name: 'default'
        workloadProfileType: 'D4'
        minimumCount: 1
        maximumCount: 2
      }
    ]
  }
}

resource uaiAzureRambiAcrPull 'Microsoft.ManagedIdentity/userAssignedIdentities@2022-01-31-preview' = {
  name: 'azure-rambi-acr-pull'
  location: location
}

@description('This allows the managed identity of the container app to access the registry, note scope is applied to the wider ResourceGroup not the ACR')
resource uaiRbacAcrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, uaiAzureRambiAcrPull.id, 'ACR Pull Role RG')
  scope: resourceGroup()
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalId: uaiAzureRambiAcrPull.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

//Shared secrets for the container apps
var shared_secrets = [
  {
    name: 'appinsight-inst-key'
    value: applicationInsights.outputs.instrumentationKey
  }
  {
    name: 'applicationinsights-connection-string'
    value: applicationInsights.outputs.connectionString
  }
  {
    name: 'apim-subscription-key'
    value: apiManagement.outputs.apiAdminSubscriptionKey
  }
]

@description('Creates an Movie Poster SVC Azure Container App.')
module containerMoviePosterSvcApp 'modules/apps/movie-poster-svc.bicep' = {
  name: 'movie-poster-svc'
  params: {
    location: location
    containerName: 'movie-poster-svc'
    containerPort: 8002
    containerRegistryName: containerRegistry.name
    acrPullRoleName: uaiAzureRambiAcrPull.name
    shared_secrets: shared_secrets
    containerAppsEnvironment: containerAppsEnv.name
    storageContributorRoleName: azrStorageContributor.name
    additionalProperties: [
      {
        name: 'AZURE_OPENAI_ENDPOINT'
        value: 'https://${apiManagement.outputs.apiManagementProxyHostName}/azure-openai'
      }
      {
        name: 'APIM_ENDPOINT'
        value: apiManagement.outputs.apiManagementProxyHostName
      }
      {
        name: 'REDIS_HOST'
        value: redis.outputs.redisHost
      }
      {
        name: 'REDIS_PORT'
        value: '${int('${redis.outputs.redisPort}')}'
      }
      {
        name: 'USE_CACHE'
        value: 'oui'
      }
      {
        name: 'STORAGE_ACCOUNT_BLOB_URL'
        value: storageAccountAzureRambi.properties.primaryEndpoints.blob
      }
      {
        name: 'AZURE_CLIENT_ID_BLOB'
        value: azrStorageContributor.properties.clientId
      }
    ]
  }
}

@description('Creates an GUI SVC Azure Container App.')
module containerGuiSvcApp 'modules/apps/gui-svc.bicep' = {
  name: 'gui-svc'
  params: {
    location: location
    containerName: 'gui-svc'
    containerPort: 8000
    containerRegistryName: containerRegistry.name
    acrPullRoleName: uaiAzureRambiAcrPull.name
    shared_secrets: shared_secrets
    containerAppsEnvironment: containerAppsEnv.name
    additionalProperties: [
      {
        name: 'AZURE_OPENAI_ENDPOINT'
        value: 'https://${apiManagement.outputs.apiManagementProxyHostName}/azure-openai'
      }
      {
        name: 'TMDB_ENDPOINT'
        value: 'https://${apiManagement.outputs.apiManagementProxyHostName}'
      }
      {
        name: 'REDIS_HOST'
        value: redis.outputs.redisHost
      }
      {
        name: 'REDIS_PORT'
        value: '${int('${redis.outputs.redisPort}')}'
      }
    ]
  }
}

@description('Creates an Movie Generator SVC Azure Container App.')
module containerMovieGeneratorSvcApp 'modules/apps/movie-generator-svc.bicep' = {
  name: 'movie-generator-svc'
  params: {
    location: location
    containerName: 'movie-generator-svc'
    containerPort: 8001
    containerRegistryName: containerRegistry.name
    acrPullRoleName: uaiAzureRambiAcrPull.name
    shared_secrets: shared_secrets
    containerAppsEnvironment: containerAppsEnv.name
    additionalProperties: [
      {
        name: 'AZURE_OPENAI_ENDPOINT'
        value: 'https://${apiManagement.outputs.apiManagementProxyHostName}/azure-openai'
      }
      {
        name: 'APIM_ENDPOINT'
        value: apiManagement.outputs.apiManagementProxyHostName
      }
    ]
  }
}

@description('Creates a Movie Gallery Azure Container App.')
module containerMovieGallerySvcApp 'modules/apps/movie-gallery-svc.bicep' = {
  name: 'movie-gallery-svc'
  params: {
    location: location
    containerName: 'movie-gallery-svc'
    containerPort: 80
    containerRegistryName: containerRegistry.name
    acrPullRoleName: uaiAzureRambiAcrPull.name
    shared_secrets: shared_secrets
    containerAppsEnvironment: containerAppsEnv.name
    storageAccountName: storageAccountAzureRambi.name
  }
}

@description('Creates an Azure Storage Account.')
resource storageAccountAzureRambi 'Microsoft.Storage/storageAccounts@2021-09-01' = {
  name: 'azrambi${uniqueString(resourceGroup().id)}'
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    allowSharedKeyAccess: false
    networkAcls: {
      bypass: 'AzureServices'
      virtualNetworkRules: []
      ipRules: []
      defaultAction: 'Allow'
    }
  }

  resource blobServices 'blobServices' = {
    resource container 'containers' = {
      name: 'movieposters'
      properties: {
        publicAccess: 'None'
      }
    }
    name: 'default'
  }

  resource queueServices 'queueServices' = {
    resource queue 'queues' = {
      name: 'movieposters-events'
      properties: {}
    }
    name: 'default'
  }
}

resource azrStorageContributor 'Microsoft.ManagedIdentity/userAssignedIdentities@2018-11-30' = {
  name: 'azure-rambi-storage-contributor'
  location: location
}

// Define the Storage Blob Data Contributor role
resource storageBlobDataContributorRoleDefinition 'Microsoft.Authorization/roleDefinitions@2018-01-01-preview' existing = {
  scope: subscription()
  name: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
}

resource assignroleAssignment 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  scope: storageAccountAzureRambi
  name: guid(resourceGroup().id, azrStorageContributor.id, storageBlobDataContributorRoleDefinition.id)
  properties: {
    roleDefinitionId: storageBlobDataContributorRoleDefinition.id
    principalId: azrStorageContributor.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

module systemTopic 'br/public:avm/res/event-grid/system-topic:0.6.0' = {
  name: 'systemTopicDeployment'
  params: {
    // Required parameters
    name: 'azrambi-event-grid-topic'
    source: storageAccountAzureRambi.id
    topicType: 'Microsoft.Storage.StorageAccounts'
    // Non-required parameters
    location:  location
    eventSubscriptions: [
      {
        destination: {
          endpointType: 'StorageQueue'
          properties: {
            queueMessageTimeToLiveInSeconds: 86400
            resourceId: storageAccountAzureRambi.id
            queueName: 'movieposters-events'
          }
        }
        eventDeliverySchema: 'CloudEventSchemaV1_0'
        expirationTimeUtc: '2099-01-01T11:00:21.715Z'
        filter: {
          enableAdvancedFilteringOnArrays: true
          isSubjectCaseSensitive: false
        }
        name: 'movieposters-event-subscription'
        retryPolicy: {
          eventTimeToLive: '120'
          maxDeliveryAttempts: 10
        }
      }
    ]
  }
}

module userPortalAccess 'modules/user_portal_role.bicep' = {
  name: 'user-portal-access'
  params: {
    kvName: kv.name
    storageAccountName: storageAccountAzureRambi.name
  }
}

output AZURE_LOCATION string = location
output AZURE_CONTAINER_ENVIRONMENT_NAME string = containerAppsEnv.name
output AZURE_CONTAINER_REGISTRY_NAME string = containerRegistry.name
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.properties.loginServer
output APIM_SUBSCRIPTION_KEY string = apiManagement.outputs.apiAdminSubscriptionKey
output APIM_ENDPOINT string = apiManagement.outputs.apiManagementProxyHostName
output MOVIE_POSTER_ENDPOINT string = 'https://${containerMoviePosterSvcApp.outputs.fqdn}'
output MOVIE_GENERATOR_ENDPOINT string = 'https://${containerMovieGeneratorSvcApp.outputs.fqdn}'
output MOVIE_GALLERY_ENDPOINT string = 'https://${containerMovieGallerySvcApp.outputs.fqdn}'
output OPENAI_API_VERSION string = '2024-08-01-preview'
output AZURE_OPENAI_ENDPOINT string = 'https://${apiManagement.outputs.apiManagementProxyHostName}/azure-openai'
output AZURE_OPENAI_API_KEY string = apiManagement.outputs.apiAdminSubscriptionKey
output APIM_SERVICE_NAME string = apiManagement.name
output TMDB_ENDPOINT string = apiManagement.outputs.apiManagementProxyHostName
