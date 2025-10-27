param aiFoundryAccountName string // Name of the AI Foundry account
param aiFoundryProjectName string // Name of the AI Foundry project  
param managedIdentityPrincipalId string // Principal ID for the Managed Identity
param principalType string = 'ServicePrincipal' // Default to Service Principal for Managed Identity

var aiFoundryAiUserId = '53ca6127-db72-4b80-b1b0-d745d6d5456d' //Azure AI User

// Reference the existing AI Foundry account
resource aiFoundryAccount 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: aiFoundryAccountName
}

// Reference the existing AI Foundry project
resource aiFoundryProject 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' existing = {
  parent: aiFoundryAccount
  name: aiFoundryProjectName
}

// Role assignment for AI Foundry Project - Managed Identity
resource aiFoundryRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aiFoundryProject.id, managedIdentityPrincipalId, aiFoundryAiUserId)
  scope: aiFoundryProject
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', aiFoundryAiUserId)
    principalId: managedIdentityPrincipalId
    principalType: principalType
  }
}

