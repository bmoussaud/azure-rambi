@description('Location of the resources')
param location string = resourceGroup().location

@description('Model deployments for OpenAI')
param deployments array = [
  {
    name: 'gpt-4o'
    capacity: 40
    version: '2024-08-06' //2024-08-06 ?
  }
  {
    name: 'text-embedding-ada-002'
    capacity: 120
    version: '2'
  }
  {
    name: 'dall-e-3'
    model: 'dall-e-3'
    version: '3.0'
    capacity: 1
  }
]

@description('Restore the service instead of creating a new instance. This is useful if you previously soft-deleted the service and want to restore it. If you are restoring a service, set this to true. Otherwise, leave this as false.')
param restore bool = false

@description('The email address of the owner of the service')
var apimPublisherEmail = 'azure-rambi@contososuites.com'

var apiManagementServiceName = 'azure-rambi-apim-${uniqueString(resourceGroup().id)}'
var apimSku = 'Basicv2'
var apimSkuCount = 1
var apimPublisherName = 'Azure Rambi Suites'

var openAIName = 'azrambi-openai-${uniqueString(resourceGroup().id)}'
var acrName = 'azurerambi${uniqueString(resourceGroup().id)}'
var storageAccountName = 'azrambi${uniqueString(resourceGroup().id)}'
var kvName = 'azrambikv${uniqueString(resourceGroup().id)}'

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
      name: 'Standard'
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
  name: kvName
  location: location
  properties: {
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    sku: {
      name: 'standard'
      family: 'A'
    }
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
    publicNetworkAccess: 'Disabled'
  }
}

resource vaultAccess 'Microsoft.ManagedIdentity/userAssignedIdentities@2018-11-30' = {
  name: 'azure-rambi-vault-access'
  location: location
}

@description('This is the built-in Key Vault Administrator role. See https://docs.microsoft.com/azure/role-based-access-control/built-in-roles#key-vault-administrator')
resource keyVaultAdministratorRoleDefinition 'Microsoft.Authorization/roleDefinitions@2018-01-01-preview' existing = {
  scope: subscription()
  name: '00482a5a-887f-4fb3-b363-3b7fe8e74483'
}

@description('This is the built-in Key Vault Secrets Officer role. See https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/security#key-vault-secrets-officer')
resource keyVaultSecretsOfficerRoleDefinition 'Microsoft.Authorization/roleDefinitions@2018-01-01-preview' existing = {
  scope: subscription()
  name: 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7'
}

@description('Assigns the API Management service the role to browse and read the keys of the Key Vault.')
resource apiManagementKeyVaultRoleAssignment 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid(kv.id, 'apiManagement', 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7')
  scope: kv
  properties: {
    roleDefinitionId: keyVaultSecretsOfficerRoleDefinition.id
    principalId: apiManagement.outputs.apiManagementIdentityPrincipalId
  }
}

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
      '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
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
    aiName: 'azure-rambi-appIn-${uniqueString(resourceGroup().id)}'
    eventHubNamespaceName: 'azure-rambi-ehn-${uniqueString(resourceGroup().id)}'
    eventHubName: 'azure-rambi-eh-${uniqueString(resourceGroup().id)}'
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
    apiPath: '/azure-openai/openai'
    openApiJson: 'https://raw.githubusercontent.com/bmoussaud/azure-rambi/refs/heads/main/src/apim/definition/azure_open_ai.json'
    openApiXml: 'https://raw.githubusercontent.com/bmoussaud/azure-rambi/refs/heads/main/src/apim/policies/azure_open_ai.xml'
    serviceUrlPrimary: '${openAI.properties.endpoint}/openai'
    apiSubscriptionName: 'azure-rambi-sub'
    aiLoggerName: 'aiLogger'
  }
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

module logAnalyticsWorkspace 'modules/log-analytics-workspace.bicep' = {
  name: 'log-analytics-workspace'
  params: {
    location: location
    logAnalyticsName: 'azure-rambi-log-${uniqueString(resourceGroup().id)}'
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
    workspaceName: 'azure-rambi-log-${uniqueString(resourceGroup().id)}'
    applicationInsightsName: 'azure-rambi-appIn-${uniqueString(resourceGroup().id)}'
  }
  dependsOn: [
    logAnalyticsWorkspace
  ]
}

module redis 'modules/redis.bicep' = {
  name: 'redis-cache'
  params: {
    location: location
    redisCacheName: 'azure-rambi-cache-${uniqueString(resourceGroup().id)}'
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

  properties: {
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
var acrPullRole = resourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')

@description('This allows the managed identity of the container app to access the registry, note scope is applied to the wider ResourceGroup not the ACR')
resource uaiRbacAcrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, uaiAzureRambiAcrPull.id, acrPullRole)
  properties: {
    roleDefinitionId: acrPullRole
    principalId: uaiAzureRambiAcrPull.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

@description('Creates an Movie Poster SVC Azure Container App.')
resource containerMoviePosterSvcApp 'Microsoft.App/containerApps@2024-10-02-preview' = {
  name: 'movie-poster-svc'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${uaiAzureRambiAcrPull.id}': {}
      '${azrStorageContributor.id}': {}
    }
  }
  tags: { 'azd-service-name': 'movie_poster_svc' }
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    workloadProfileName: 'default'
    configuration: {
      ingress: {
        external: true
        targetPort: 3100
        allowInsecure: false
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      secrets: [
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
          name: 'redis-password'
          value: redis.outputs.redisPassword
        }
        {
          name: 'storage-account-connection-string'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
        }
      ]
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
              name: 'REDIS_PASSWORD'
              secretRef: 'redis-password'
            }
            {
              name: 'USE_CACHE'
              value: 'oui'
            }
            {
              name: 'STORAGE_ACCOUNT_CONNECTION_STRING'
              secretRef: 'storage-account-connection-string'
            }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/liveness'
                port: 3100
              }
            }

            {
              type: 'Readiness'
              httpGet: {
                path: '/readiness'
                port: 3100
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
resource guirSvcApp 'Microsoft.App/containerApps@2024-10-02-preview' = {
  name: 'gui-svc'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${uaiAzureRambiAcrPull.id}': {}
    }
  }
  tags: { 'azd-service-name': 'gui' }
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    workloadProfileName: 'default'
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        allowInsecure: false
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      secrets: [
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
          name: 'gui'
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          env: [
            {
              name: 'OPENAI_API_VERSION'
              value: '2024-08-01-preview'
            }
            {
              name: 'AZURE_OPENAI_API_KEY'
              value: '-1'
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: 'https://${apiManagement.outputs.apiManagementProxyHostName}/azure-openai'
            }
            {
              name: 'MOVIE_POSTER_ENDPOINT'
              value: 'http://movie-poster-svc'
            }
            {
              name: 'MOVIE_GENERATOR_ENDPOINT'
              value: 'http://movie-generator-svc'
            }
            {
              name: 'APIM_SUBSCRIPTION_KEY'
              secretRef: 'apim-subscription-key'
            }
            {
              name: 'TMDB_ENDPOINT'
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
              value: 'gui'
            }
            {
              name: 'OTEL_RESOURCE_ATTRIBUTES'
              value: 'service.namespace=azure-rambi,service.instance.id=gui-svc'
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

@description('Creates an Movie Generator SVC Azure Container App.')
resource containerMovieGeneratorSvcApp 'Microsoft.App/containerApps@2024-10-02-preview' = {
  name: 'movie-generator-svc'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${uaiAzureRambiAcrPull.id}': {}
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
      secrets: [
        {
          name: 'azure-openai-endpoint'
          value: 'https://${apiManagement.outputs.apiManagementProxyHostName}/azure-openai'
        }
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
              name: 'MOVIE_POSTER_ENDPOINT'
              value: 'http://movie-poster-svc'
            }
            {
              name: 'AZURE_OPENAI_API_KEY'
              secretRef: 'apim-subscription-key'
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              secretRef: 'azure-openai-endpoint'
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

@description('Creates an Azure Storage Account.')
resource storageAccount 'Microsoft.Storage/storageAccounts@2021-09-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    allowSharedKeyAccess: true
  }
}

// Create a Blob service in the storage account
resource moviepostersStorageService 'Microsoft.Storage/storageAccounts/blobServices@2021-09-01' = {
  name: 'default'
  parent: storageAccount
}
//Create a container in the storage account
resource moviepostersStorageContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2021-09-01' = {
  name: 'movieposters'
  parent: moviepostersStorageService
}

resource contributorRoleDefinition 'Microsoft.Authorization/roleDefinitions@2018-01-01-preview' existing = {
  scope: subscription()
  // This is the Storage Account Contributor role, which is the minimum role permission we can give. See https://docs.microsoft.com/en-us/azure/role-based-access-control/built-in-roles#:~:text=17d1049b-9a84-46fb-8f53-869881c3d3ab
  name: '17d1049b-9a84-46fb-8f53-869881c3d3ab'
}

resource azrStorageContributor 'Microsoft.ManagedIdentity/userAssignedIdentities@2018-11-30' = {
  name: 'azure-rambi-storage-contributor'
  location: location
}

resource assignroleAssignment 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  scope: storageAccount
  name: guid(resourceGroup().id, azrStorageContributor.id, contributorRoleDefinition.id)
  properties: {
    roleDefinitionId: contributorRoleDefinition.id
    principalId: azrStorageContributor.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

output movieserviceFQDN string = containerMoviePosterSvcApp.properties.configuration.ingress.fqdn
output guiFQDN string = guirSvcApp.properties.configuration.ingress.fqdn
output moviegeneratorFQDN string = containerMovieGeneratorSvcApp.properties.configuration.ingress.fqdn
output AZURE_LOCATION string = location

output AZURE_CONTAINER_ENVIRONMENT_NAME string = containerAppsEnv.name
output AZURE_CONTAINER_REGISTRY_NAME string = containerRegistry.name
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.properties.loginServer

output STORAGE_ACCOUNT_KEY string = storageAccount.listKeys().keys[0].value
output STORAGE_ACCOUNT_NAME string = storageAccount.name
output STORAGE_ACCOUNT_CONNECTION_STRING string = 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
output APIM_SUBSCRIPTION_KEY string = apiManagement.outputs.apiAdminSubscriptionKey
output APIM_ENDPOINT string = apiManagement.outputs.apiManagementProxyHostName
output MOVIE_POSTER_ENDPOINT string = containerMoviePosterSvcApp.properties.configuration.ingress.fqdn
output MOVIE_GENERATOR_ENDPOINT string = containerMovieGeneratorSvcApp.properties.configuration.ingress.fqdn
output OPENAI_API_VERSION string = '2024-08-01-preview'
output AZURE_OPENAI_ENDPOINT string = 'https://${apiManagement.outputs.apiManagementProxyHostName}/azure-openai'
output AZURE_OPENAI_API_KEY string = apiManagement.outputs.apiAdminSubscriptionKey
