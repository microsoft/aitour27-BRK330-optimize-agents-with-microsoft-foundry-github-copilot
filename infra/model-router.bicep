targetScope = 'resourceGroup'

@description('Existing Microsoft Foundry account name.')
param foundryAccountName string

@minValue(1)
@description('Global Standard Model Router capacity in thousands of tokens per minute.')
param capacity int = 200

resource foundry 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: foundryAccountName
}

resource modelRouter 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = {
  parent: foundry
  name: 'model-router'
  sku: {
    name: 'GlobalStandard'
    capacity: capacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'model-router'
      version: '2025-11-18'
    }
  }
}

output deploymentName string = modelRouter.name
output deploymentModel string = modelRouter.properties.model.name
output deploymentVersion string = modelRouter.properties.model.version
output deploymentCapacity int = modelRouter.sku.capacity
