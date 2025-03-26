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

param kvName string = 'azure-rambi-kv'

param containerName string = 'movie-gallery-svc'
param containerPort int = 5000

param location string = resourceGroup().location

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' existing = {
  name: containerRegistryName
}

resource kv 'Microsoft.KeyVault/vaults@2024-04-01-preview' existing = {
  name: kvName
}

resource uaiAzureRambiAcrPull 'Microsoft.ManagedIdentity/userAssignedIdentities@2022-01-31-preview' existing = {
  name: acrPullRoleName
}

resource containerAppsEnv 'Microsoft.App/managedEnvironments@2024-10-02-preview' existing = {
  name: containerAppsEnvironment
  resource daprComponent 'daprComponents@2022-03-01' = {
    name: containerName
    properties: {
      componentType: 'state.azure.cosmosdb'
      version: 'v1'
      initTimeout: '5m'
      secrets: [
        {
          name: 'cosmos-key'
          value: 'https://${kv.name}.vault.azure.net/secrets/cosmosAccountMasterKey'
        }
      ]
      metadata: [
        {
          name: 'url'
          value: cosmosAccount.outputs.endpoint
        }
        {
          name: 'masterKey'
          secretRef: 'cosmos-key'
        }
        {
          name: 'database'
          value: containerName
        }
        {
          name: 'collection'
          value: 'state'
        }
        {
          name: 'actorStateStore'
          value: 'true'
        }
      ]
      scopes: [
        containerName
      ]
    }
  }
}

/*
module containerMovieGallerySvcApp 'br/public:avm/res/app/container-app:0.14.1' = {
  name: containerName
  params: {
    // Required parameters
    environmentResourceId: containerAppsEnv.id
    tags: { 'azd-service-name': replace(containerName, '-', '_') }
    name: containerName
    exposedPort: containerPort
    managedIdentities: {
      userAssignedResourceIds: userIdentityIds
    }
    registries: [
      {
        server: containerRegistry.properties.loginServer
      }
    ]
    secrets: concat(shared_secrets, [
      {
        name: 'appinsight-inst-key'
        secretUri: 'https://${kv.name}.vault.azure.net/secrets/appinsight-inst-key'
      }
    ])
    containers: [
      {
        image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
        name: containerName
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

        resources: {
          cpu: '0.5'
          memory: '1.0Gi'
        }
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
  }
}
*/

resource containerMovieGallerySvcApp 'Microsoft.App/containerApps@2024-10-02-preview' = {
  name: containerName
  location: location
  identity: {
    type: 'UserAssigned'
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
        appPort: containerPort
        enableApiLogging: true
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

module cosmosAccount 'br/public:avm/res/document-db/database-account:0.11.3' = {
  name: 'databaseAccountDeployment'
  params: {
    // Required parameters
    name: 'azure-rambi-cosmos-account'
    // Non-required parameters
    location: location
    secretsExportConfiguration: {
      keyVaultResourceId: kv.id
      primaryWriteKeySecretName: 'cosmosAccountMasterKey'
      primaryReadOnlyKeySecretName: 'cosmosAccountMasterReadKey'
      primaryWriteConnectionStringSecretName: 'cosmosAccountConnectionString'
      primaryReadonlyConnectionStringSecretName: 'cosmosAccountReadConnectionString'
    }
    sqlDatabases: [
      {
        name: containerName
        containers: [
          {
            name: 'state'
            paths: [
              '/partitionKey'
            ]
          }
        ]
      }
    ]
  }
}

output name string = containerMovieGallerySvcApp.name
output fqdn string = containerMovieGallerySvcApp.properties.configuration.ingress.fqdn
