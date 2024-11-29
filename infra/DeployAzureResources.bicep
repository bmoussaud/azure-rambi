@description('Location of the resources')
param location string = resourceGroup().location

@description('Model deployments for OpenAI')
param deployments array = [
  {
    name: 'gpt-4o'
    capacity: 40
    version: '2024-05-13'
  }
  {
    name: 'text-embedding-ada-002'
    capacity: 120
    version: '2'
  }
]


@description('Restore the service instead of creating a new instance. This is useful if you previously soft-deleted the service and want to restore it. If you are restoring a service, set this to true. Otherwise, leave this as false.')
param restore bool = false

@description('The email address of the owner of the service')
@minLength(1)
param apimPublisherEmail string = 'support@contososuites.com'

var apiManagementServiceName = 'apim-${uniqueString(resourceGroup().id)}'
var apimSku = 'Basicv2'
var apimSkuCount = 1
var apimPublisherName = 'Contoso Suites'

var webAppNameApi = '${uniqueString(resourceGroup().id)}-api'
var webAppNameDash = '${uniqueString(resourceGroup().id)}-dash'
var webAppSku = 'S1'
var appServicePlanName = '${uniqueString(resourceGroup().id)}-cosu-asp'

var openAIName = '${uniqueString(resourceGroup().id)}-openai'

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
  name: webAppNameApi
  location: location
  kind: 'linux'
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    clientAffinityEnabled: false
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.12' // Specify Python version
      http20Enabled: true
      minTlsVersion: '1.2'
      appCommandLine: 'gunicorn azurerambi.app:app --bind=0.0.0.0 --chdir src'
      appSettings: [
        {
          name: 'OPENAI_API_VERSION'
          value: '2024-02-01'
        }
        {
          name: 'AZURE_OPENAI_API_KEY'
          value: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
        }
        {
          name: 'AZURE_OPENAI_ENDPOINT'
          value: 'https://${openAI.name}.search.windows.net'
        }
        {
          name: 'TMBDTMDB_API_KEY'
          value: '68d40b1b40c8ba0c137374cf5dc3e7a1'
        }
        {
          name: 'TMDB_CACHE_ENABLED'
          value: 'true'
        }
        ]
      }
    }
}



