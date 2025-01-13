@description('Location of the resources')
param location string = resourceGroup().location

@description('The name of the Redis Cache instance')
param redisCacheName string

resource redisCache 'Microsoft.Cache/redis@2020-06-01' = {
  name: redisCacheName
  location: location
  sku: {
    name: 'Standard'
    family: 'C'
    capacity: 1
  }
  properties: {
    enableNonSslPort: false
  }
}

output redisHost string = redisCache.properties.hostName
output redisPort int = 6379
output redisPassword string = listKeys(redisCache.id, '2020-06-01').primaryKey
