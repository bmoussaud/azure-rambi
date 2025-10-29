@description('Primary location for all resources')
param location string

@description('Name of the Container Apps Environment')
param environmentName string

@description('Key Vault Contributor Managed Identity ID')
param keyVaultContributorIdentityId string

@description('Application Insights instrumentation key')
@secure()
param appInsightsInstrumentationKey string

@description('Application Insights connection string')
@secure()
param appInsightsConnectionString string

@description('Log Analytics workspace customer ID')
param logAnalyticsCustomerId string

@description('Log Analytics workspace primary shared key')
@secure()
param logAnalyticsPrimarySharedKey string

@description('Creates an Azure Container Apps Environment.')
resource containerAppsEnv 'Microsoft.App/managedEnvironments@2024-10-02-preview' = {
  name: environmentName
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${keyVaultContributorIdentityId}': {}
    }
  }

  properties: {
    daprAIInstrumentationKey: appInsightsInstrumentationKey

    appInsightsConfiguration: {
      connectionString: appInsightsConnectionString
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
        customerId: logAnalyticsCustomerId
        sharedKey: logAnalyticsPrimarySharedKey
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

output environmentName string = containerAppsEnv.name
output environmentId string = containerAppsEnv.id
