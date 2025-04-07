@minLength(1)
@description('Primary location for all resources')
param location string

@description('Restore the service instead of creating a new instance. This is useful if you previously soft-deleted the service and want to restore it. If you are restoring a service, set this to true. Otherwise, leave this as false.')
param restore bool = false

@description('The email address of the owner of the service')
var apimPublisherEmail = 'azure-rambi@contososuites.com'

var apiManagementServiceName = 'azrambi-apim-${uniqueString(resourceGroup().id)}'
var apimSku = 'Basicv2'
var apimSkuCount = 1
var apimPublisherName = 'Azure Rambi Suites'

var openAIName = 'azrambi-openai-${uniqueString(resourceGroup().id)}'
var acrName = 'azurerambi${uniqueString(resourceGroup().id)}'
var storageAccountName = 'azrambi${uniqueString(resourceGroup().id)}'

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
    serviceName: apiManagementServiceName
    publisherName: apimPublisherName
    publisherEmail: apimPublisherEmail
    skuName: apimSku
    skuCount: apimSkuCount
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
    redisContributorName: 'azure-rambi-storage-contributor'
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
resource containerMoviePosterSvcApp 'Microsoft.App/containerApps@2024-10-02-preview' = {
  name: 'movie-poster-svc'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${uaiAzureRambiAcrPull.id}': {}
      '${azrStorageContributor.id}': {}
      '${azrQueueStorageProducer.id}': {}
    }
  }
  tags: { 'azd-service-name': 'movie_poster_svc' }
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    workloadProfileName: 'default'
    configuration: {
      ingress: {
        external: true
        targetPort: 8002
        allowInsecure: false
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      secrets: shared_secrets
      registries: [
        {
          identity: uaiAzureRambiAcrPull.id
          server: containerRegistry.properties.loginServer
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'movie-poster-svc'
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          env: [
            {
              name: 'OPENAI_API_VERSION'
              value: '2024-08-01-preview'
            }
            {
              name: 'AZURE_OPENAI_API_KEY'
              secretRef: 'apim-subscription-key'
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: 'https://${apiManagement.outputs.apiManagementProxyHostName}/azure-openai'
            }
            {
              name: 'APIM_SUBSCRIPTION_KEY'
              secretRef: 'apim-subscription-key'
            }
            {
              name: 'APIM_ENDPOINT'
              value: apiManagement.outputs.apiManagementProxyHostName
            }
            {
              name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
              secretRef: 'appinsight-inst-key'
            }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              secretRef: 'applicationinsights-connection-string'
            }
            {
              name: 'ApplicationInsightsAgent_EXTENSION_VERSION'
              value: '~3'
            }
            {
              name: 'OTEL_SERVICE_NAME'
              value: 'movie_poster_svc'
            }
            {
              name: 'OTEL_RESOURCE_ATTRIBUTES'
              value: 'service.namespace=azure-rambi,service.instance.id=movie-poster-svc'
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
              name: 'STORAGE_ACCOUNT_QUEUE_URL'
              value: storageAccountAzureRambi.properties.primaryEndpoints.queue
            }
            {
              // Required for managed identity to access the storage account
              name: 'AZURE_CLIENT_ID_BLOB'
              value: azrStorageContributor.properties.clientId
            }
            {
              name: 'AZURE_CLIENT_ID_QUEUE'
              value: azrQueueStorageProducer.properties.clientId
            }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/liveness'
                port: 8002
              }
            }

            {
              type: 'Readiness'
              httpGet: {
                path: '/readiness'
                port: 8002
              }
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 2
      }
    }
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
resource containerMovieGeneratorSvcApp 'Microsoft.App/containerApps@2024-10-02-preview' = {
  name: 'movie-generator-svc'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${uaiAzureRambiAcrPull.id}': {}
      '${azrStorageContributor.id}': {}
    }
  }
  tags: { 'azd-service-name': 'movie_generator_svc' }
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    workloadProfileName: 'default'
    configuration: {
      ingress: {
        external: true
        targetPort: 8001
        allowInsecure: false
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      secrets: shared_secrets
      registries: [
        {
          identity: uaiAzureRambiAcrPull.id
          server: containerRegistry.properties.loginServer
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'movie-generator-svc'
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          env: [
            {
              name: 'OPENAI_API_VERSION'
              value: '2024-08-01-preview'
            }
            {
              name: 'MOVIE_POSTER_ENDPOINT'
              value: 'http://movie-poster-svc'
            }
            {
              name: 'AZURE_OPENAI_API_KEY'
              secretRef: 'apim-subscription-key'
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: 'https://${apiManagement.outputs.apiManagementProxyHostName}/azure-openai'
            }
            {
              name: 'APIM_SUBSCRIPTION_KEY'
              secretRef: 'apim-subscription-key'
            }
            {
              name: 'APIM_ENDPOINT'
              value: apiManagement.outputs.apiManagementProxyHostName
            }
            {
              name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
              secretRef: 'appinsight-inst-key'
            }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              secretRef: 'applicationinsights-connection-string'
            }
            {
              name: 'ApplicationInsightsAgent_EXTENSION_VERSION'
              value: '~3'
            }
            {
              name: 'OTEL_SERVICE_NAME'
              value: 'movie_generator_svc'
            }
            {
              name: 'OTEL_RESOURCE_ATTRIBUTES'
              value: 'service.namespace=azure-rambi,service.instance.id=movie-generator-svc'
            }
            {
              // Required for managed identity to access the storage account
              name: 'AZURE_CLIENT_ID'
              value: azrStorageContributor.properties.clientId
            }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/liveness'
                port: 8001
              }
            }

            {
              type: 'Readiness'
              httpGet: {
                path: '/readiness'
                port: 8001
              }
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 2
      }
    }
  }
}

@description('Creates a Movie Gallery Azure Container App.')
module containerMovieGallerySvcApp 'modules/apps/movie-gallery-svc.bicep' = {
  name: 'movie-gallery-svc'
  params: {
    location: location
    containerName: 'movie-gallery-svc'
    containerPort: 5000
    containerRegistryName: containerRegistry.name
    acrPullRoleName: uaiAzureRambiAcrPull.name
    shared_secrets: shared_secrets
    containerAppsEnvironment: containerAppsEnv.name
  }
}

@description('Creates an Azure Storage Account.')
resource storageAccountAzureRambi 'Microsoft.Storage/storageAccounts@2021-09-01' = {
  name: storageAccountName
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
      name: 'generatedmovies'
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

resource rambiEventsHandler 'Microsoft.Web/sites@2024-04-01' = {
  name: 'rambi-events-handler'
  location: location
  tags: { 'azd-service-name': 'rambi-events-handler' }
  kind: 'functionapp,linux,container,azurecontainerapps'
  //appInsightResourceId : applicationInsights.outputs.id
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${uaiAzureRambiAcrPull.id}': {} // ACR pull
      '${azfctStorageContributor.id}': {} // Internal Azure Function Storage access
      '${azrQueueStorageReader.id}': {} // Storage access To the Queue
    }
  }

  properties: {
    managedEnvironmentId: containerAppsEnv.id
    siteConfig: {
      linuxFxVersion: 'DOCKER|mcr.microsoft.com/azure-functions/dotnet8-quickstart-demo:1.0'
      //linuxFxVersion: 'DOCKER|azurerambieab45rexk4hhs.azurecr.io/azure-rambi/rambi_event_handler_local:396bbb31'
      acrUseManagedIdentityCreds: true
      acrUserManagedIdentityID: uaiAzureRambiAcrPull.id
      appSettings: [
        {
          name: 'DOCKER_REGISTRY_SERVER_URL'
          value: containerRegistry.properties.loginServer
        }
        {
          name: 'RambiQueueStorageConnection__credential'
          value: 'managedidentity'
        }
        {
          name: 'RambiQueueStorageConnection__clientId'
          value: azrQueueStorageReader.properties.clientId
        }
        {
          name: 'RambiQueueStorageConnection__queueServiceUri'
          value: storageAccountAzureRambi.properties.primaryEndpoints.queue
        }
        {
          name: 'RambiQueueStorageConnection__accountName'
          value: storageAccountAzureRambi.name
        }
        {
          name: 'RambiQueueStorageConnection__accountKey'
          value: storageAccountAzureRambi.listKeys().keys[0].value
        }
        {
          name: 'RambiQueueStorageConnection__queueEndpoint'
          value: storageAccountAzureRambi.properties.primaryEndpoints.queue
        }
        {
          name: 'RambiQueueStorageConnection__blobEndpoint'
          value: storageAccountAzureRambi.properties.primaryEndpoints.blob
        }
        {
          name: 'AzureWebJobsStorage'
          value: 'managedidentity'
        }
        {
          name: 'AzureWebJobsStorage__accountName'
          value: functionStorageAccount.name
        }
        {
          name: 'AzureWebJobsStorage__accountKey'
          value: functionStorageAccount.listKeys().keys[0].value
        }
        {
          name: 'AzureWebJobsStorage__queueEndpoint'
          value: functionStorageAccount.properties.primaryEndpoints.queue
        }
        {
          name: 'AzureWebJobsStorage__blobEndpoint'
          value: functionStorageAccount.properties.primaryEndpoints.blob
        }
        {
          name: 'AzureWebJobsStorage__clientId'
          value: azfctStorageContributor.properties.clientId
        }
        {
          name: 'AzureWebJobsStorage__credential'
          value: 'managedidentity'
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: applicationInsights.outputs.instrumentationKey
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: applicationInsights.outputs.connectionString
        }
        {
          name: 'PYTHON_ENABLE_WORKER_EXTENSIONS'
          value: '1'
        }
        {
          name: 'MOVIE_GALLERY_SVC_ENDPOINT'
          value: 'https://${containerMovieGallerySvcApp.outputs.fqdn}'
        }
      ]
    }
  }
}

var resourceToken = toLower(uniqueString(subscription().id, 'dev', location))
var deploymentStorageContainerName = 'app-package-${take('azurerambi', 32)}-${take(resourceToken, 7)}'
var functionStorageAccountName = 'azrambifct${uniqueString(resourceGroup().id)}'

resource functionStorageAccount 'Microsoft.Storage/storageAccounts@2021-09-01' = {
  name: functionStorageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
  }

  resource blobServices 'blobServices' = {
    resource container 'containers' = {
      name: deploymentStorageContainerName
      properties: {
        publicAccess: 'None'
      }
    }
    name: 'default'
  }
}

resource azfctStorageContributor 'Microsoft.ManagedIdentity/userAssignedIdentities@2018-11-30' = {
  name: 'azure-fct-storage-contributor'
  location: location
}

resource azrQueueStorageReader 'Microsoft.ManagedIdentity/userAssignedIdentities@2018-11-30' = {
  name: 'azure-rambi-queue-storage-reader'
  location: location
}

resource azrQueueStorageProducer 'Microsoft.ManagedIdentity/userAssignedIdentities@2018-11-30' = {
  name: 'azure-rambi-queue-storage-producer'
  location: location
}

// Assign the Storage Queue Data Contributor and Storage Queue Data Message Processor roles to the function app
resource assignroleAssignmentTriggerStorageAccount 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = [
  for roleId in [
    '19e7f393-937e-4f77-808e-94535e297925' // Storage Queue Data Reader
    '8a0f0c08-91a1-4084-bc3d-661d67233fed' // Storage Queue Data Message Processor
  ]: {
    name: guid(storageAccountAzureRambi.id, azrQueueStorageReader.id, roleId)
    scope: storageAccountAzureRambi
    properties: {
      roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleId)
      principalId: azrQueueStorageReader.properties.principalId
      principalType: 'ServicePrincipal'
    }
  }
]

resource assignroleAssignmentMessageProducterStorageAccount 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = [
  for roleId in [
    '974c5e8b-45b9-4653-ba55-5f855dd0fb88' // Storage queue Data Contributor
    'c6a89b2d-59bc-44d0-9896-0f6e12d7b80a' // Storage Queue Data Message Sender
  ]: {
    name: guid(storageAccountAzureRambi.id, azrQueueStorageProducer.id, roleId)
    scope: storageAccountAzureRambi
    properties: {
      roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleId)
      principalId: azrQueueStorageProducer.properties.principalId
      principalType: 'ServicePrincipal'
    }
  }
]

// Assign the Storage Blob Data Owner and Storage Blob Data Contributor roles to the function app
resource assignroleAssignmentFunctionStorageAccount 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = [
  for roleId in [
    'b7e6dc6d-f1e8-4753-8033-0f276bb0955b' // Storage Blob Data Owner
    'ba92f5b4-2d11-453d-a403-e96b0029c9fe' // Storage Blob Data Contributor
    '0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3' // Storage Queue Data Contributor
  ]: {
    name: guid(functionStorageAccount.id, azfctStorageContributor.id, roleId)
    scope: functionStorageAccount
    properties: {
      roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleId)
      principalId: azfctStorageContributor.properties.principalId
      principalType: 'ServicePrincipal'
    }
  }
]

output AZURE_LOCATION string = location
output AZURE_CONTAINER_ENVIRONMENT_NAME string = containerAppsEnv.name
output AZURE_CONTAINER_REGISTRY_NAME string = containerRegistry.name
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.properties.loginServer
output APIM_SUBSCRIPTION_KEY string = apiManagement.outputs.apiAdminSubscriptionKey
output APIM_ENDPOINT string = apiManagement.outputs.apiManagementProxyHostName
output MOVIE_POSTER_ENDPOINT string = 'https://${containerMoviePosterSvcApp.properties.configuration.ingress.fqdn}'
output MOVIE_GENERATOR_ENDPOINT string = 'https://${containerMovieGeneratorSvcApp.properties.configuration.ingress.fqdn}'
output MOVIE_GALLERY_ENDPOINT string = 'https://${containerMovieGallerySvcApp.outputs.fqdn}'
output OPENAI_API_VERSION string = '2024-08-01-preview'
output AZURE_OPENAI_ENDPOINT string = 'https://${apiManagement.outputs.apiManagementProxyHostName}/azure-openai'
output AZURE_OPENAI_API_KEY string = apiManagement.outputs.apiAdminSubscriptionKey
output APIM_SERVICE_NAME string = apiManagementServiceName
output TMDB_ENDPOINT string = apiManagement.outputs.apiManagementProxyHostName
