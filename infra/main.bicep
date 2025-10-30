@minLength(1)
@description('Primary location for all resources')
param location string

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@description('Location for AI Foundry resources.')
param aiFoundryLocation string = 'eastus2' //'westus' 'switzerlandnorth' swedencentral

var rootname = 'azrambi'

module aiFoundry 'modules/ai-foundry.bicep' = {
  name: 'aiFoundryModel'
  params: {
    name: '${rootname}-${environmentName}'
    location: aiFoundryLocation
    modelDeploymentsParameters: [
      {
        name: 'gpt-4o'
        model: 'gpt-4o'
        capacity: 100
        deployment: 'GlobalStandard'
        version: '2024-08-06'
        format: 'OpenAI'
      }
      /*
         {
        name: 'dall-e-3'
        model: 'dall-e-3'
        capacity: 1
        deployment: 'Standard'
        version: '3.0'
        format: 'OpenAI'
      }
        */
      {
        name: 'o1-mini'
        model: 'o1-mini'
        capacity: 10
        deployment: 'GlobalStandard'
        version: '2024-09-12'
        format: 'OpenAI'
      }

      {
        name: 'gpt-image-1'
        model: 'gpt-image-1'
        capacity: 3
        deployment: 'GlobalStandard'
        version: '2025-04-15'
        format: 'OpenAI'
      }
    ]
  }
}

module aiFoundryProject 'modules/ai-foundry-project.bicep' = {
  name: 'aiFoundryProject'
  params: {
    location: aiFoundryLocation
    aiFoundryName: aiFoundry.outputs.aiFoundryName
    aiProjectName: '${rootname}-${aiFoundryLocation}'
    aiProjectFriendlyName: '${rootname} Project ${environmentName}'
    aiProjectDescription: 'Azure Rambi Suites AI Foundry Project'
    applicationInsightsName: applicationInsights.outputs.aiName
    storageName: storageAccountAzureRambi.outputs.name
  }
}

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
resource azrKeyVaultContributor 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' = {
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
  scope: resourceGroup()
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
    serviceUrlPrimary: aiFoundry.outputs.aiFoundryEndpoint
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

module serviceBus 'modules/service-bus.bicep' = {
  name: 'service-bus'
  params: {
    location: location
    serviceBusNamespaceName: 'azure-rambi-sb-${uniqueString(resourceGroup().id)}'
    managedIdentityName: azrAppsMi.name
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
    redisContributorName: azrAppsMi.name
  }
}

@description('Creates an Azure Container Registry.')
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: '${rootname}${uniqueString(resourceGroup().id)}'
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
  tags: {
    displayName: 'Container Registry'
    'container.registry': '${rootname}${uniqueString(resourceGroup().id)}'
  }
}

module containerAppsEnv 'modules/container-apps-environment.bicep' = {
  name: 'container-apps-environment'
  params: {
    location: location
    environmentName: 'azure-rambi'
    keyVaultContributorIdentityId: azrKeyVaultContributor.id
    appInsightsInstrumentationKey: applicationInsights.outputs.instrumentationKey
    appInsightsConnectionString: applicationInsights.outputs.connectionString
    logAnalyticsCustomerId: logAnalyticsWorkspace.outputs.customerId
    logAnalyticsPrimarySharedKey: logAnalyticsWorkspace.outputs.primarySharedKey
    
  }
}

module daprComponents 'modules/dapr-components.bicep' = {
  name: 'daprComponents'
  params: {
    location: location
    containerAppsEnvironmentName: containerAppsEnv.outputs.environmentName
    storageAccountName: storageAccountAzureRambi.outputs.name
    azureRambiAppsManagedIdentityName: azrAppsMi.name
    cosmosDbAccountDocumentEndpoint: cosmosDb.outputs.documentEndpoint
    serviceBusNamespaceName: serviceBus.outputs.serviceBusNamespaceName
  }
}

resource uaiAzureRambiAcrPull 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' = {
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
  {
    name: 'azure-openai-api-key'
    value: aiFoundry.outputs.aiFoundryApiKey
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
    containerAppsEnvironment: containerAppsEnv.outputs.environmentName
    azureRambiAppsManagedIdentityName: azrAppsMi.name
    additionalProperties: [
      {
        name: 'AZURE_OPENAI_ENDPOINT'
        value: aiFoundry.outputs.aiFoundryEndpoint
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
        value: 'no'
      }

      {
        name: 'STORAGE_ACCOUNT_BLOB_URL'
        value: storageAccountAzureRambi.outputs.primaryBlobEndpoint
      }
      {
        name: 'AZURE_CLIENT_ID_BLOB'
        value: azrAppsMi.properties.clientId
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
    containerAppsEnvironment: containerAppsEnv.outputs.environmentName
    additionalProperties: [
      {
        name: 'AZURE_OPENAI_ENDPOINT'
        value: aiFoundry.outputs.aiFoundryEndpoint
      }
      {
        name: 'TMDB_ENDPOINT'
        value: 'https://${apiManagement.outputs.apiManagementProxyHostName}'
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
    azureRambiAppsManagedIdentityName: azrAppsMi.name
    shared_secrets: shared_secrets
    containerAppsEnvironment: containerAppsEnv.outputs.environmentName
    additionalProperties: [
      {
        name: 'AZURE_OPENAI_ENDPOINT'
        value: aiFoundry.outputs.aiFoundryEndpoint
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
    containerAppsEnvironment: containerAppsEnv.outputs.environmentName
    azureRambiAppsManagedIdentityName: azrAppsMi.name
    additionalProperties: [
      {
        name: 'STORAGE_ACCOUNT_NAME'
        value: storageAccountAzureRambi.name
      }
      {
        name: 'STORAGE_QUEUE_NAME'
        value: 'movieposters-events'
      }
    ]
  }
  dependsOn: [
    daprComponents
  ]
}


module cosmosDb 'modules/cosmosdb.bicep' = {
  name: 'cosmosdb-deployment'
  params: {
    name: 'azrambi-cosmosdb-${uniqueString(resourceGroup().id)}'
    location: 'Central US'
    logAnalyticsWorkspaceResourceId: logAnalyticsWorkspace.outputs.id
    managedIdentityPrincipalId: azrAppsMi.properties.principalId 
    databases: [
      {
        name: 'azrambi-db'
        throughput: 400
        containers: [
          {
            name: 'movies'
            paths: ['/partitionKey']
          }
           {
            name: 'validations'
            paths: ['/partitionKey']
          }
        ]
      }
    ]
  }
}

@description('Creates a Movie Poster Agent Azure Container App.')
module containerMoviePosterAgentSvcApp 'modules/apps/movie-poster-agent-svc.bicep' = {
  name: 'movie-poster-agent-svc'
  params: {
    location: location
    containerName: 'movie-poster-agent-svc'
    containerPort: 8005
    containerRegistryName: containerRegistry.name
    acrPullRoleName: uaiAzureRambiAcrPull.name
    azureRambiAppsManagedIdentityName: azrAppsMi.name
    shared_secrets: shared_secrets
    containerAppsEnvironment: containerAppsEnv.outputs.environmentName
    
    additionalProperties: [
      {
        name: 'AZURE_OPENAI_ENDPOINT'
        value: aiFoundry.outputs.aiFoundryEndpoint
      }
      {
        name: 'AZURE_AI_PROJECT_ENDPOINT'
        value: aiFoundryProject.outputs.projectEndpoint
      }
      {
        name: 'AZURE_AI_MODEL_DEPLOYMENT'
        value: 'gpt-4o'
      }

      {
        name: 'STORAGE_ACCOUNT_BLOB_URL'
        value: storageAccountAzureRambi.outputs.primaryBlobEndpoint
      }
      {
        name: 'AZURE_CLIENT_ID'
        value: azrAppsMi.properties.clientId
      }
    ]
  }
  dependsOn: [
    daprComponents
  ]
}

module storageAccountAzureRambi 'br/public:avm/res/storage/storage-account:0.27.1' = {
  name: 'azrambi-storage-account'

  params: {
    name: 'azrambi${uniqueString(resourceGroup().id)}'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false // Disable local authentication methods as per policy
    dnsEndpointType: 'Standard'
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
    blobServices: {
      containers: [
        { name: 'movieposters', publicAccess: 'None' }
      ]
    }
    queueServices: {
      queues: [
        { name: 'movieposters-events' }
      ]
    }
    roleAssignments: [
      {
        principalId: az.deployer().objectId
        principalType: 'User'
        roleDefinitionIdOrName: 'Storage Blob Data Contributor'
      }
      {
        principalId: azrAppsMi.properties.principalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: 'Storage Blob Data Contributor'
      }
      {
        principalId: azrAppsMi.properties.principalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: 'Storage Queue Data Contributor'
      }
    ]

    minimumTlsVersion: 'TLS1_2' // Enforcing TLS 1.2 for better security
    location: location
  }
}
resource azrAppsMi 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' = {
  name: 'azure-rambi-apps'
  location: location
}

module rbacAgentFoundry 'modules/rbac_agent_foundry.bicep' = {
  name: 'rbac-agent-foundry-assignment'
  params: {
    aiFoundryAccountName: aiFoundry.outputs.aiFoundryName
    aiFoundryProjectName: aiFoundryProject.outputs.projectName
    managedIdentityPrincipalId: azrAppsMi.properties.principalId
  }
}

module systemTopic 'br/public:avm/res/event-grid/system-topic:0.6.0' = {
  name: 'systemTopicDeployment'
  params: {
    // Required parameters
    name: 'azrambi-event-grid-topic'
    source: storageAccountAzureRambi.outputs.resourceId
    topicType: 'Microsoft.Storage.StorageAccounts'
    // Non-required parameters
    location: location
    eventSubscriptions: [
      {
        destination: {
          endpointType: 'StorageQueue'
          properties: {
            queueMessageTimeToLiveInSeconds: 86400
            resourceId: storageAccountAzureRambi.outputs.resourceId
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

/*
module userPortalAccess 'modules/user_portal_role.bicep' = {
  name: 'user-portal-access'
  params: {
    kvName: kv.name
    storageAccountName: storageAccountAzureRambi.outputs.name
  }
}*/

output AZURE_LOCATION string = location
output AZURE_CONTAINER_ENVIRONMENT_NAME string = containerAppsEnv.outputs.environmentName
output AZURE_CONTAINER_REGISTRY_NAME string = containerRegistry.name
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.properties.loginServer
output APIM_SUBSCRIPTION_KEY string = apiManagement.outputs.apiAdminSubscriptionKey
output APIM_ENDPOINT string = apiManagement.outputs.apiManagementProxyHostName
output MOVIE_POSTER_ENDPOINT string = 'https://${containerMoviePosterSvcApp.outputs.fqdn}'
output MOVIE_POSTER_AGENT_ENDPOINT string = 'https://${containerMoviePosterAgentSvcApp.outputs.fqdn}'
output MOVIE_GENERATOR_ENDPOINT string = 'https://${containerMovieGeneratorSvcApp.outputs.fqdn}'
output MOVIE_GALLERY_ENDPOINT string = 'https://${containerMovieGallerySvcApp.outputs.fqdn}'
output GUI_ENDPOINT string = 'https://${containerGuiSvcApp.outputs.fqdn}'
output OPENAI_API_VERSION string = '2024-08-01-preview'
output AZURE_OPENAI_ENDPOINT string = aiFoundry.outputs.aiFoundryEndpoint
output AZURE_OPENAI_API_KEY string = aiFoundry.outputs.aiFoundryApiKey
output APIM_SERVICE_NAME string = apiManagement.name
output TMDB_ENDPOINT string = 'https://${apiManagement.outputs.apiManagementProxyHostName}'
output STORAGE_ACCOUNT_BLOB_URL string = storageAccountAzureRambi.outputs.primaryBlobEndpoint
output AZURE_AI_PROJECT_ENDPOINT string = aiFoundryProject.outputs.projectEndpoint
output AZURE_CLIENT_ID string = azrAppsMi.properties.clientId
