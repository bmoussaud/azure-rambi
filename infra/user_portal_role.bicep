var kvName = 'rambikv${uniqueString(resourceGroup().id)}'
var storageAccountName = 'azrambi${uniqueString(resourceGroup().id)}'

resource kv 'Microsoft.KeyVault/vaults@2024-04-01-preview' existing = {
  name: kvName
}
@description('This is the built-in Key Vault Secrets Officer role. See https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles/security#key-vault-secrets-user')
resource keyVaultSecretsUserRoleDefinition 'Microsoft.Authorization/roleDefinitions@2018-01-01-preview' existing = {
  scope: subscription()
  name: '4633458b-17de-408a-b874-0445c86b69e6'
}

//https://praveenkumarsreeram.com/2024/12/12/introducing-az-deployer-objectid-in-bicep-track-object-principle-id-of-user-managed-identity/
//https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/bicep-functions-deployment#deployer
//Not implemented yet in AZD https://github.com/Azure/azure-dev/issues/4620
@description('Assigns the API Management service the role to browse and read the keys of the Key Vault to the deployer')
//seful to check information about the KN in the Azure portal 
resource keyVaultSecretUserRoleAssignmentOnDeployer 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid(kv.id, 'Deployer', keyVaultSecretsUserRoleDefinition.id)
  scope: kv
  properties: {
    roleDefinitionId: keyVaultSecretsUserRoleDefinition.id
    //Principal ID of the current user
    principalId: az.deployer().objectId
  }
}

resource storageAccount 'Microsoft.Storage/storageAccounts@2021-09-01' existing = {
  name: storageAccountName
}

resource storageBlobDataContributorRoleDefinition 'Microsoft.Authorization/roleDefinitions@2018-01-01-preview' existing = {
  scope: subscription()
  name: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
}

resource assignroleAssignment 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  scope: storageAccount
  name: guid(resourceGroup().id, 'Deployer', storageBlobDataContributorRoleDefinition.id)
  properties: {
    roleDefinitionId: storageBlobDataContributorRoleDefinition.id
    principalId: az.deployer().objectId
  }
}
