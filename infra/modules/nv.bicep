param apimName string
param keyName string
param value string

resource parentAPIM 'Microsoft.ApiManagement/service@2023-03-01-preview' existing = {
  name: apimName
}

resource apiKey 'Microsoft.ApiManagement/service/namedValues@2021-08-01' = {
  name: keyName
  parent: parentAPIM
  properties: {
    displayName: keyName
    value: value
    secret: true
  }
}


