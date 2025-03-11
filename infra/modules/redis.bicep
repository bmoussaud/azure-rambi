@description('Location of the resources')
param location string = resourceGroup().location

@description('The name of the Redis Cache instance')
param redisCacheName string

@description('The name of the user assigned identity to be used as the storage contributor.')
param redisContributorName string = ''

@description('The pricing tier of the new Azure Redis Cache.')
@allowed([
  'Basic'
  'Standard'
])
param cacheSKUName string = 'Basic'

@description('The family for the sku.')
@allowed([
  'C'
])
param cacheSKUFamily string = 'C'

@description('The size of the new Azure Redis Cache instance. ')
@minValue(0)
@maxValue(6)
param cacheSKUCapacity int = 0

@description('Specify name of Built-In access policy to use as assignment.')
@allowed([
  'Data Owner'
  'Data Contributor'
  'Data Reader'
])
param builtInAccessPolicyName string = 'Data Owner'

//TO DO: move to  'Microsoft.Cache/redisEnterprise@2024-09-01-preview' = {
//https://luke.geek.nz/azure/deploying-azure-managed-redis-with-bicep/
//https://learn.microsoft.com/en-us/azure/azure-cache-for-redis/managed-redis/managed-redis-overview?WT.mc_id=AZ-MVP-5004796
//fAster to provision

resource redisCache 'Microsoft.Cache/Redis@2024-11-01' = {
  name: redisCacheName
  location: location

  properties: {
    disableAccessKeyAuthentication: true
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
    redisConfiguration: {
      'aad-enabled': 'true'
    }
    sku: {
      name: cacheSKUName
      family: cacheSKUFamily
      capacity: cacheSKUCapacity
    }
  }
}

resource redisCacheBuiltInAccessPolicyAssignment 'Microsoft.Cache/redis/accessPolicyAssignments@2023-08-01' = {
  name: '${builtInAccessPolicyName}-${uniqueString(resourceGroup().id)}'
  parent: redisCache
  properties: {
    accessPolicyName: builtInAccessPolicyName
    objectId: redisContributor.properties.principalId
    objectIdAlias: redisContributor.name
  }
}

resource redisContributor 'Microsoft.ManagedIdentity/userAssignedIdentities@2018-11-30' existing = {
  name: redisContributorName
}

output redisHost string = redisCache.properties.hostName
output redisPort int = redisCache.properties.sslPort
