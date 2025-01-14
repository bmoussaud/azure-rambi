@description('Location of the resources')
param location string = resourceGroup().location

resource containerMoviePosterSvcApp 'Microsoft.App/containerApps@2024-10-02-preview' existing = {
  name: 'movie-poster-svc'
}

resource redisCache 'Microsoft.Cache/Redis@2021-06-01' existing = {
  name: 'azure-rambi-cache-b76s6utvi44xo'
}

resource myBenoitRedis 'Microsoft.ServiceLinker/linkers@2024-07-01-preview' = {
  name: 'myBenoitRedis'
  scope: containerMoviePosterSvcApp

  properties: {
    clientType: 'python'
    targetService: {
      //type: 'AzureCacheForRedis'
      //id: '/subscriptions/9479b396-5d3e-467a-b89f-ba8400aeb7dd/resourceGroups/azrambi/providers/Microsoft.Cache/Redis/azure-rambi-cache-b76s6utvi44xo/databases/0'
      id: redisCache.id
      type: 'AzureResource'
    }
  }
}

/*
{
  status: 'Failed'
  error: {
    code: 'TargetTypeNotSupported'
    message: 'Target resource type MICROSOFT.CACHE/REDIS is not supported.'
  }
}
*/
