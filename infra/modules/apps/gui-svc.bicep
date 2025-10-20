param location string
param containerName string
param containerPort int
param containerRegistryName string
param acrPullRoleName string
param shared_secrets array
param containerAppsEnvironment string

@description('Additional properties to be added to the container app')
param additionalProperties array = []

resource uaiAzureRambiAcrPull 'Microsoft.ManagedIdentity/userAssignedIdentities@2022-01-31-preview' existing = {
  name: acrPullRoleName
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' existing = {
  name: containerRegistryName
}

resource containerAppsEnv 'Microsoft.App/managedEnvironments@2024-10-02-preview' existing = {
  name: containerAppsEnvironment
}

resource guirSvcApp 'Microsoft.App/containerApps@2024-10-02-preview' = {
  name: 'gui-svc'
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
          env: concat(
            [
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
            ],
            additionalProperties
          )
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 2
      }
    }
  }
}

output fqdn string = guirSvcApp.properties.configuration.ingress.fqdn
