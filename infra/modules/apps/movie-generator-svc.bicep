@description('Location for the resources')
param location string
param containerName string
param containerPort int
param containerRegistryName string
param acrPullRoleName string

param shared_secrets array
param containerAppsEnvironment string
param additionalProperties array = []

resource acrPullRole 'Microsoft.ManagedIdentity/userAssignedIdentities@2018-11-30' existing = {
  name: acrPullRoleName
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' existing = {
  name: containerRegistryName
}

resource containerAppsEnv 'Microsoft.App/managedEnvironments@2024-10-02-preview' existing = {
  name: containerAppsEnvironment
}

resource containerApp 'Microsoft.App/containerApps@2024-10-02-preview' = {
  name: containerName
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${acrPullRole.id}': {}
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
          identity: acrPullRole.id
          server: containerRegistry.properties.loginServer
        }
      ]
    }
    template: {
      containers: [
        {
          name: containerName
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          env: concat(
            [
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
            ],
            additionalProperties
          )
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

output fqdn string = containerApp.properties.configuration.ingress.fqdn
