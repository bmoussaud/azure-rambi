param storageAccountName string
param managedIdentityPrincipalId string // Principal ID for the Managed Identity
param principalType string = 'ServicePrincipal' // Default to Service Principal for Managed Identity

resource storageAccount 'Microsoft.Storage/storageAccounts@2022-09-01' existing = {
  name: storageAccountName
}


var storageStorageBlobDataOwnerRoleDefinitionId  = 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b' //Storage Blob Data Owner role
var storageBlobDataContributorRoleDefinitionId = 'ba92f5b4-2d11-453d-a403-e96b0029c9fe' // Storage Blob Data Contributor role


// Role assignment for Storage Account (Blob) - Managed Identity
resource storageRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' =  {
  name: guid(storageAccount.id, managedIdentityPrincipalId, storageStorageBlobDataOwnerRoleDefinitionId) // Use managed identity ID
  scope: storageAccount
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', storageStorageBlobDataOwnerRoleDefinitionId)
    principalId: managedIdentityPrincipalId // Use managed identity ID
    principalType: principalType// Managed Identity is a Service Principal
  }
}

resource storageRoleAssignmentStorageBlobDataContributorRoleDefinitionId 'Microsoft.Authorization/roleAssignments@2022-04-01' =  {
  name: guid(storageAccount.id, managedIdentityPrincipalId, storageBlobDataContributorRoleDefinitionId) // Use managed identity ID
  scope: storageAccount
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', storageBlobDataContributorRoleDefinitionId)
    principalId: managedIdentityPrincipalId // Use managed identity ID
    principalType: principalType // Managed Identity is a Service Principal
  }
}
