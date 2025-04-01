targetScope = 'resourceGroup'

// ------------------
//    PARAMETERS
// ------------------
@description('Container apps environment id where the container app will be deployed')
param containerAppsEnvironment string

@description('Shared secrets for the container app.')
param shared_secrets array = []

@description('User identity IDs for the container app.')
param acrPullRoleName string = ''

@description('Azure Container Registry name.')
param containerRegistryName string

param containerName string = 'movie-gallery-svc'
param containerPort int = 5000

param location string = resourceGroup().location

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' existing = {
  name: containerRegistryName
}

resource uaiAzureRambiAcrPull 'Microsoft.ManagedIdentity/userAssignedIdentities@2022-01-31-preview' existing = {
  name: acrPullRoleName
}

resource containerAppsEnv 'Microsoft.App/managedEnvironments@2024-10-02-preview' existing = {
  name: containerAppsEnvironment
  resource statestoreComponent 'daprComponents@2022-03-01' = {
    name: '${containerName}-statetore'

    properties: {
      componentType: 'state.azure.cosmosdb'
      version: 'v1'
      initTimeout: '5m'
      secrets: []
      metadata: [
        {
          name: 'url'
          value: cosmosDbAccount.properties.documentEndpoint
        }
        {
          name: 'database'
          value: containerName
        }
        {
          name: 'collection'
          value: 'state'
        }
      ]
      scopes: [
        containerName
      ]
    }
  }
}

resource containerMovieGallerySvcApp 'Microsoft.App/containerApps@2024-10-02-preview' = {
  name: containerName
  location: location
  identity: {
    type: 'SystemAssigned,UserAssigned'
    userAssignedIdentities: {
      '${uaiAzureRambiAcrPull.id}': {}
    }
  }
  tags: { 'azd-service-name': replace(containerName, '-', '_') }
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    workloadProfileName: 'default'
    configuration: {
      ingress: {
        external: true
        targetPort: containerPort
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
      dapr: {
        enabled: true
        appId: containerName
        appProtocol: 'http'
        appPort: containerPort
        enableApiLogging: true
        logLevel: 'info'
      }
    }
    template: {
      containers: [
        {
          name: containerName
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          env: [
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
              value: containerName
            }
            {
              name: 'OTEL_RESOURCE_ATTRIBUTES'
              value: 'service.namespace=azure-rambi,service.instance.id=${containerName}'
            }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/liveness'
                port: containerPort
              }
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/readiness'
                port: containerPort
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

resource cosmosDbAccount 'Microsoft.DocumentDB/databaseAccounts@2022-08-15' = {
  name: 'azrambi-cosmos-account'
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    databaseAccountOfferType: 'Standard'
    publicNetworkAccess: 'Enabled'
  }
}

resource cosmosDbDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2021-04-15' = {
  name: containerName
  parent: cosmosDbAccount
  properties: {
    resource: {
      id: containerName
    }
  }
}

resource cosmosDbDatabaseCollection 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2021-05-15' = {
  name: 'state'
  parent: cosmosDbDatabase

  properties: {
    resource: {
      id: 'state'
      partitionKey: {
        paths: [
          '/partitionKey'
        ]
        kind: 'Hash'
      }
    }
    options: {
      autoscaleSettings: {
        maxThroughput: 4000
      }
    }
  }
}

// Assign cosmosdb account read/write access to aca system assigned identity
// To know more: https://learn.microsoft.com/azure/cosmos-db/how-to-setup-rbac
resource backendApiService_cosmosdb_role_assignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2022-08-15' = {
  name: guid(subscription().id, containerMovieGallerySvcApp.name, '00000000-0000-0000-0000-000000000002')
  parent: cosmosDbAccount
  properties: {
    principalId: containerMovieGallerySvcApp.identity.principalId
    roleDefinitionId: resourceId(
      'Microsoft.DocumentDB/databaseAccounts/sqlRoleDefinitions',
      cosmosDbAccount.name,
      '00000000-0000-0000-0000-000000000002'
    ) //DocumentDB Data Contributor
    scope: '${cosmosDbAccount.id}/dbs/${cosmosDbDatabase.name}/colls/${cosmosDbDatabaseCollection.name}'
  }
}

output name string = containerMovieGallerySvcApp.name
output fqdn string = containerMovieGallerySvcApp.properties.configuration.ingress.fqdn
