targetScope = 'resourceGroup'

@description('Azure Managed Identity name')
param azureRambiAppsManagedIdentityName string 

@description('Primary location for all resources')
param location string = resourceGroup().location

@description('Container app name')
param containerName string

resource azrAppsMi 'Microsoft.ManagedIdentity/userAssignedIdentities@2022-01-31-preview' existing = {
  name: azureRambiAppsManagedIdentityName
}

resource cosmosDbAccount 'Microsoft.DocumentDB/databaseAccounts@2022-08-15' = {
  name: 'azrambi-cosmos-dbaccount'
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    databaseAccountOfferType: 'Standard'
    publicNetworkAccess: 'Enabled'
    // Allow access from Azure datacenters (Container Apps have dynamic IPs)
    ipRules: [
      {
        ipAddressOrRange: '0.0.0.0'
      }
    ]
    isVirtualNetworkFilterEnabled: false
    enableAutomaticFailover: false
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
  }
}

resource cosmosDbDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2021-04-15' = {
  name: containerName
  parent: cosmosDbAccount
  properties: {
    resource: {
      id: containerName
    }
  }
}

resource cosmosDbDatabaseCollection 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2021-05-15' = {
  name: 'state'
  parent: cosmosDbDatabase

  properties: {
    resource: {
      id: 'state'
      partitionKey: {
        paths: [
          '/partitionKey'
        ]
        kind: 'Hash'
      }
    }
    options: {
      autoscaleSettings: {
        maxThroughput: 4000
      }
    }
  }
}

// Assign cosmosdb account read/write access to aca system assigned identity
// To know more: https://learn.microsoft.com/azure/cosmos-db/how-to-setup-rbac
resource azrAppsMi_cosmosdb_role_assignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2022-08-15' = {
  name: guid(
    subscription().id,
    'docdbcontributor',
    cosmosDbDatabaseCollection.name,
    '00000000-0000-0000-0000-000000000002'
  )
  parent: cosmosDbAccount
  properties: {
    principalId: azrAppsMi.properties.principalId
    roleDefinitionId: resourceId(
      'Microsoft.DocumentDB/databaseAccounts/sqlRoleDefinitions',
      cosmosDbAccount.name,
      '00000000-0000-0000-0000-000000000002'
    ) //DocumentDB Data Contributor
    scope: '${cosmosDbAccount.id}/dbs/${cosmosDbDatabase.name}/colls/${cosmosDbDatabaseCollection.name}'
  }
}

resource user_cosmosdb_role_assignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2022-08-15' = {
  name: guid(
    az.deployer().objectId,
    'docdbcontributor',
    cosmosDbDatabaseCollection.name,
    '00000000-0000-0000-0000-000000000002'
  )
  parent: cosmosDbAccount
  properties: {
    principalId: az.deployer().objectId
    roleDefinitionId: resourceId(
      'Microsoft.DocumentDB/databaseAccounts/sqlRoleDefinitions',
      cosmosDbAccount.name,
      '00000000-0000-0000-0000-000000000002'
    ) //DocumentDB Data Contributor
    scope: '${cosmosDbAccount.id}/dbs/${cosmosDbDatabase.name}/colls/${cosmosDbDatabaseCollection.name}'
  }
}



output name string = cosmosDbAccount.name
output docummentEndpoint string = cosmosDbAccount.properties.documentEndpoint

