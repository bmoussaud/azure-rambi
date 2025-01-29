@description('Location of the resources')
param location string = resourceGroup().location
resource containerAppsEnv 'Microsoft.App/managedEnvironments@2024-10-02-preview' existing = {
  name: 'azure-rambi'
}
var acrName = 'azurerambi${uniqueString(resourceGroup().id)}'
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' existing = {
  name: acrName
}
resource uaiAzureRambiAcrPull 'Microsoft.ManagedIdentity/userAssignedIdentities@2022-01-31-preview' existing = {
  name: 'azure-rambi-acr-pull'
}
var functionStorageAccountName = 'azrambifct${uniqueString(resourceGroup().id)}'

resource rambiEventsHandler 'Microsoft.Web/sites@2022-09-01' = {
  name: 'rambi-events-handler'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${uaiAzureRambiAcrPull.id}': {}
      '${azfctStorageContributor.id}': {}
    }
  }
  tags: { 'azd-service-name': 'rambi-events-handler' }
  kind: 'functionapp,linux,container,azurecontainerapps'
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    siteConfig: {
      linuxFxVersion: 'DOCKER|azurerambitfnbpycbnkdum.azurecr.io/azurefunctionsimage:v1.0.1'
      acrUseManagedIdentityCreds: true
      acrUserManagedIdentityID: uaiAzureRambiAcrPull.id
      // minimumElasticInstanceCount: 1
      // functionAppScaleLimit: 5
      appSettings: [
        {
          name: 'DOCKER_REGISTRY_SERVER_URL'
          value: containerRegistry.properties.loginServer
        }
        {
          name: 'AzureWebJobsStorage__credential'
          value: 'managedidentity'
        }
        {
          name: 'AzureWebJobsStorage'
          value: functionStorageAccount.properties.primaryEndpoints.queue
        }

        {
          name: 'AzureWebJobsStorage__accountName'
          value: functionStorageAccount.name
        }

        // {
        //   name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
        //   value: '@Microsoft.KeyVault(SecretUri=${kv.properties.vaultUri}secrets/APPINSIGHTS-INSTRUMENTATIONKEY)'
        // }
      ]
    }
  }
}

resource functionStorageAccount 'Microsoft.Storage/storageAccounts@2021-09-01' = {
  name: functionStorageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
}

resource azfctStorageContributor 'Microsoft.ManagedIdentity/userAssignedIdentities@2018-11-30' = {
  name: 'azure-fct-storage-contributor'
  location: location
}
// Define the Storage Blob Data Contributor role
resource storageBlobDataContributorRoleDefinition 'Microsoft.Authorization/roleDefinitions@2018-01-01-preview' existing = {
  scope: subscription()
  name: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
}

resource assignroleAssignment 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  scope: functionStorageAccount
  name: guid(resourceGroup().id, azfctStorageContributor.id, storageBlobDataContributorRoleDefinition.id)
  properties: {
    roleDefinitionId: storageBlobDataContributorRoleDefinition.id
    principalId: azfctStorageContributor.properties.principalId
    principalType: 'ServicePrincipal'
  }
}
