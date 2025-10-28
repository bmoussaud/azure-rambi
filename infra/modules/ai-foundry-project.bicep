// Creates an Azure AI resource with proxied endpoints for the Azure AI services provider

@description('Azure region of the deployment')
param location string

@description('AI Foundry name')
param aiFoundryName string

@description('AI Project name')
param aiProjectName string

@description('AI Project display name')
param aiProjectFriendlyName string = aiProjectName

@description('AI Project description')
param aiProjectDescription string

param applicationInsightsName string

// @description('Storage account name.')
param storageName string

// resource storageAccount 'Microsoft.Storage/storageAccounts@2022-09-01' existing = {
//   name: storageAccountName
// }

resource aiFoundry 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: aiFoundryName
}

resource applicationInsights 'Microsoft.Insights/components@2020-02-02-preview' existing = {
  name: applicationInsightsName
}

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' existing = {
  name: storageName
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  parent: aiFoundry
  name: aiProjectName
  location: location
  
  properties: {
    description: aiProjectDescription
    displayName: aiProjectFriendlyName
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// Creates the Azure Foundry connection to your Azure App Insights resource
resource connectionAppInsight 'Microsoft.CognitiveServices/accounts/projects/connections@2025-06-01' = {
  name: 'appinsights-connection'
  parent: project
  properties: {
    category: 'AppInsights'
    target: applicationInsights.id
    authType: 'ApiKey'
    //isSharedToAll: true
    credentials: {
      key: applicationInsights.properties.ConnectionString
    }
    metadata: {
      ApiType: 'Azure'
      ResourceId: applicationInsights.id
    }
  }
}


resource project_connection_azure_storage 'Microsoft.CognitiveServices/accounts/projects/connections@2025-04-01-preview' = {
  name: storageName
  parent: project
  properties: {
    category: 'AzureBlob'
    target: storageAccount.properties.primaryEndpoints.blob
    // target: storageAccountTarget
    authType: 'AAD'
    metadata: {
      ApiType: 'Azure'
      ResourceId: storageAccount.id
      location: storageAccount.location
      accountName: storageAccount.name
      containerName: 'movieposters'
    }
  }
}


// Note: Storage account connection moved to avoid conflicts during deployment
// This can be created separately after the main AI Foundry resource is stable
// resource connectionStorageAccount 'Microsoft.CognitiveServices/accounts/connections@2025-06-01' = {
//   name: '${storageAccount.name}-connection'
//   parent: aiFoundry
//   properties: {
//     category: 'StorageAccounts'
//     target: storageAccount.id
//     authType: 'AccountKey'
//     credentials: {
//       key: listKeys(storageAccount.id, storageAccount.apiVersion).keys[0].value
//     }
//     metadata: {}
//   }
// }

output projectName string = project.name
output projectId string = project.id
output projectIdentityPrincipalId string = project.identity.principalId
output projectEndpoint string = project.properties.endpoints['AI Foundry API']
