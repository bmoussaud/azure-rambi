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
@minLength(1)
param apimPublisherEmail string = 'support@contososuites.com'

var apiManagementServiceName = 'azure-rambi-apim-${uniqueString(resourceGroup().id)}'
var apimSku = 'Basicv2'
var apimSkuCount = 1
var apimPublisherName = 'Azure Rambi Suites'

var webAppNameMain = 'azrambi-${uniqueString(resourceGroup().id)}'
var webAppSku = 'S1'
var appServicePlanName = 'azrambi-asp-${uniqueString(resourceGroup().id)}'
var openAIName = 'azrambi-openai-${uniqueString(resourceGroup().id)}'

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
resource deployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = [for deployment in deployments: {
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
}]


//Cognitive Services OpenAI User
resource cognitiveServiceOpenAIUserRoleAssignment 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name:  guid('Cognitive Services OpenAI User Role On API Management')
  scope: openAI
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
    principalId: apiManagement.outputs.apiManagementIdentityPrincipalId
  }
}


@description('Creates an Azure App Service Plan.')
resource appServicePlan 'Microsoft.Web/serverFarms@2022-09-01' = {
  name: appServicePlanName
  location: location
  kind: 'linux'
  properties: {
    reserved: true
  }
  sku: {
    name: webAppSku
  }
}

@description('Creates an Azure App Service for the API.')
resource appServiceApp 'Microsoft.Web/sites@2022-09-01' = {
  name: webAppNameMain
  location: location
  kind: 'app,linux'
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    clientAffinityEnabled: false
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.12'
      http20Enabled: true
      minTlsVersion: '1.2'
      appCommandLine: 'gunicorn azurerambi.app:app --bind=0.0.0.0 --chdir src'
      
      appSettings: [
        {
          name: 'OPENAI_API_VERSION'
          value: '2024-08-01-preview'
        }
        {
          name: 'AZURE_OPENAI_API_KEY'
          value: openAI.listKeys().key2
        }
        {
          name: 'AZURE_OPENAI_ENDPOINT'
          value: 'https://${openAI.name}.openai.azure.com'
        }
        {
          name: 'API_SUBSCRIPTION_KEY'
          value: apiManagement.outputs.apiAdminSubscriptionKey
        }
        {
          name: 'APIM_ENDPOINT'
          value: apiManagement.outputs.apiManagementProxyHostName
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
          name: 'ApplicationInsightsAgent_EXTENSION_VERSION'
          value: '~3'
        }
        ]
      }
  }
  dependsOn: [
    apiManagement
  ]
}

resource symbolicname 'Microsoft.Web/sites/config@2022-09-01' = {
  name: 'logs'
  kind: 'string'
  parent: appServiceApp
  properties: {
    applicationLogs: {
      fileSystem: {
        level: 'Information'
      }
    }
    detailedErrorMessages: {
      enabled: true
    }
    failedRequestsTracing: {
      enabled: true
    }
    httpLogs: {
      fileSystem: {
        enabled: true
      }
    }
  }
}

resource appServiceDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: '${appServiceApp.name}-diagnostics'
  properties: {
    logs: [
      {
        category: 'AppServiceHTTPLogs'
        enabled: true
      }
      {
        category: 'AppServiceConsoleLogs'
        enabled: true
        
      }
      {
        category: 'AppServiceAppLogs'
        enabled: true
        
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
    workspaceId: logAnalyticsWorkspace.outputs.id
  }
  scope: appServiceApp
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

output application_url string = appServiceApp.properties.hostNames[0]
output application_name string = appServiceApp.name

