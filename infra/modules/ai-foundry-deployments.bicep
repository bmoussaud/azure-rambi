// Module: AI Foundry Model Deployments (separated for sequencing)
@description('AI Foundry account name (existing)')
param aiFoundryName string
@description('Array of model deployment definitions')
param modelDeploymentsParameters array

// Existing AI Foundry account - assumes it was created in a prior module
resource aiFoundry 'Microsoft.CognitiveServices/accounts@2025-07-01-preview' existing = {
  name: aiFoundryName
}

// Deploy models one by one AFTER account reaches Succeeded provisioning state
// Using a stable API version for deployments
@batchSize(1)
resource modelDeployments 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = [
  for deployment in modelDeploymentsParameters: {
    parent: aiFoundry
    name: deployment.name
    sku: {
      capacity: deployment.capacity
      name: deployment.deployment
    }
    properties: {
      model: {
        format: deployment.format
        name: deployment.model
        version: deployment.version
      }
    }
  }
]

output deployedModelNames array = [for d in modelDeploymentsParameters: d.name]
