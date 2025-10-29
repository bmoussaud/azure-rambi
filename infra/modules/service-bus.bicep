param serviceBusNamespaceName string
param location string = resourceGroup().location
param skuName string = 'Standard'

@description('The name of the managed identity that will be assigned Service Bus Data Owner role')
param managedIdentityName string

resource serviceBusNamespace 'Microsoft.ServiceBus/namespaces@2021-11-01' = {
  name: serviceBusNamespaceName
  location: location
  sku: {
    name: skuName
  }
  properties: {
    disableLocalAuth: false // Allow both managed identity and connection string auth
  }
}

// Create a topic for movie updates
resource movieUpdatesTopic 'Microsoft.ServiceBus/namespaces/topics@2021-11-01' = {
  parent: serviceBusNamespace
  name: 'movie-updates'
  properties: {
    defaultMessageTimeToLive: 'P14D' // 14 days
    maxSizeInMegabytes: 1024
    requiresDuplicateDetection: false
    enableBatchedOperations: true
    supportOrdering: false
    enablePartitioning: false
  }
}

// Reference to the existing managed identity
resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: managedIdentityName
}

// Assign Azure Service Bus Data Owner role to the managed identity
resource serviceBusDataOwnerRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(serviceBusNamespace.id, managedIdentity.id, 'Azure Service Bus Data Owner')
  scope: serviceBusNamespace
  properties: {
    roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', '090c5cfd-751d-490a-894a-3ce6f1109419') // Azure Service Bus Data Owner
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

output serviceBusNamespaceName string = serviceBusNamespace.name
output serviceBusEndpoint string = serviceBusNamespace.properties.serviceBusEndpoint
output serviceBusNamespaceId string = serviceBusNamespace.id
