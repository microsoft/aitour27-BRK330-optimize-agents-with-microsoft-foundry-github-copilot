targetScope = 'resourceGroup'

@description('Existing Microsoft Foundry account name.')
param foundryAccountName string

@minValue(1)
@description('Global Standard gpt-5.4 capacity in thousands of tokens per minute.')
param capacity int = 200

resource foundry 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: foundryAccountName
}

resource teacher 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = {
  parent: foundry
  name: 'gpt-5.4'
  sku: {
    name: 'GlobalStandard'
    capacity: capacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-5.4'
      version: '2026-03-05'
    }
  }
}

output deploymentName string = teacher.name
output deploymentCapacity int = teacher.sku.capacity
