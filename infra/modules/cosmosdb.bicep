targetScope = 'resourceGroup'

import { roleAssignmentType } from 'br/public:avm/utl/types/avm-common-types:0.5.1'
import { sqlDatabaseType } from 'customTypes.bicep'

@description('Name of the Cosmos DB Account.')
param name string

@description('Specifies the location for all the Azure resources.')
param location string = resourceGroup().location

@description('Optional. Tags to be applied to the resources.')
param tags object = {}

@description('Resource ID of the Log Analytics workspace to use for diagnostic settings.')
param logAnalyticsWorkspaceResourceId string

@description('Optional. List of Cosmos DB databases to deploy.')
param databases sqlDatabaseType[] = []

@description('Optional. Array of role assignments to create.')
param roleAssignments roleAssignmentType[]?

param managedIdentityPrincipalId string // Principal ID for the Managed Identity

var nameFormatted = toLower(name)

module cosmosDb 'br/public:avm/res/document-db/database-account:0.18.0' =  {
  name: take('${nameFormatted}-cosmosdb-deployment', 64)
  #disable-next-line no-unnecessary-dependson
  
  params: {
    name: nameFormatted
    enableAutomaticFailover: false
    diagnosticSettings: [
      {
        workspaceResourceId: logAnalyticsWorkspaceResourceId
      }
    ]
    disableKeyBasedMetadataWriteAccess: true
    disableLocalAuthentication: true
    location: location
    minimumTlsVersion: 'Tls12'
    defaultConsistencyLevel: 'Session'
    networkRestrictions: {
      networkAclBypass: 'None'
      publicNetworkAccess:   'Enabled'
    }
    
    sqlDatabases: databases
    roleAssignments: roleAssignments
    
    sqlRoleAssignments: [
      {
        principalId: managedIdentityPrincipalId
        roleDefinitionId: guid(resourceGroup().id, nameFormatted, 'custom-sql-role')
      }
      
      {
        principalId: az.deployer().objectId
        roleDefinitionId: guid(resourceGroup().id, nameFormatted, 'custom-sql-role')
      }
        
    ]


    sqlRoleDefinitions: [
      {
        name: guid(resourceGroup().id, nameFormatted, 'custom-sql-role')
        //roleType: 'CustomRole'
        roleName: 'Cosmos DB Data Reader Writer'
        dataActions:[
          'Microsoft.DocumentDB/databaseAccounts/readMetadata'
          'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/*'
          'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/*'
        ]
      }
    ]

    
    tags: tags
  }
}

output resourceId string = cosmosDb.outputs.resourceId
output cosmosDBname string = cosmosDb.outputs.name
output documentEndpoint string = cosmosDb.outputs.endpoint


