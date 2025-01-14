@description('Location of the resources')
param location string = resourceGroup().location

@description('The name of the Redis Cache instance')
param redisCacheName string

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

resource redisCache 'Microsoft.Cache/Redis@2021-06-01' = {
  name: redisCacheName
  location: location

  properties: {
    sku: {
      name: cacheSKUName
      family: cacheSKUFamily
      capacity: cacheSKUCapacity
    }
  }
}

output redisHost string = redisCache.properties.hostName
output redisPort int = redisCache.properties.sslPort
output redisPassword string = listKeys(redisCache.id, '2021-06-01').primaryKey
