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

@description('Azure Managed Identity name')
param azureRambiAppsManagedIdentityName string 

@description('Azure Container Registry name.')
param containerRegistryName string

param containerName string = 'movie-gallery-svc'
param containerPort int = 5000

param additionalProperties array = []

param location string = resourceGroup().location

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' existing = {
  name: containerRegistryName
}

resource uaiAzureRambiAcrPull 'Microsoft.ManagedIdentity/userAssignedIdentities@2022-01-31-preview' existing = {
  name: acrPullRoleName
}

resource azrAppsMi 'Microsoft.ManagedIdentity/userAssignedIdentities@2022-01-31-preview' existing = {
  name: azureRambiAppsManagedIdentityName
}

resource containerAppsEnv 'Microsoft.App/managedEnvironments@2024-10-02-preview' existing = {
  name: containerAppsEnvironment
}

resource containerMovieGallerySvcApp 'Microsoft.App/containerApps@2024-10-02-preview' = {
  name: containerName
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${uaiAzureRambiAcrPull.id}': {}
      '${azrAppsMi.id}': {}
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
          env:concat( additionalProperties, [
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
            {
              name: 'PORT'
              value: '${containerPort}'
            }
          ])
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



output name string = containerMovieGallerySvcApp.name
output fqdn string = containerMovieGallerySvcApp.properties.configuration.ingress.fqdn
