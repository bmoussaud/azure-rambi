var storageAccountName = 'azrambi${uniqueString(resourceGroup().id)}'

@description('Location of the resources')
param location string = resourceGroup().location

@description('Creates an Azure Storage Account.')
resource storageAccount 'Microsoft.Storage/storageAccounts@2021-09-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    allowSharedKeyAccess: false
    defaultToAzureADAuthorization: true
    networkAcls: {
      bypass: 'AzureServices'
      virtualNetworkRules: []
      ipRules: []
      defaultAction: 'Allow'
    }
  }
}
