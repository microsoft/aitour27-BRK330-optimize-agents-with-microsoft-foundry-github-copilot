targetScope = 'resourceGroup'

@description('Learner-selected Azure deployment location.')
param location string = resourceGroup().location

@description('Short azd environment identifier.')
param environmentName string

@description('Foundry account provisioned by the microsoft.foundry provider.')
param foundryAccountName string

@description('Foundry project provisioned by the microsoft.foundry provider.')
param projectName string

@description('Selected immutable agent configuration identifier.')
param contosoConfiguration string

@description('Selected model deployment name.')
param contosoModelDeployment string

@description('Signed-in deployment principal object ID.')
param principalId string

@description('Hosted Agent immutable version identity principal ID.')
param hostedAgentInstancePrincipalId string = ''

@description('AcrPull role definition GUID for an RBAC-mode registry.')
param acrPullRoleId string

@description('Foundry Agent Consumer role definition GUID.')
param foundryAgentConsumerRoleId string

@description('Foundry User role definition GUID.')
param foundryUserRoleId string

@description('Foundry Project Manager role definition GUID.')
param foundryProjectManagerRoleId string

@description('Monitoring Metrics Publisher role definition GUID.')
param monitoringMetricsPublisherRoleId string

@description('Monitoring Reader role definition GUID.')
param monitoringReaderRoleId string

@description('Placeholder image replaced by azd deploy web.')
param webImage string = 'mcr.microsoft.com/k8se/quickstart:latest'

@description('Configure the web app to pull from the private registry after RBAC exists.')
param configureRegistry bool = false

var suffix = toLower(uniqueString(subscription().id, resourceGroup().id, environmentName))
var registryName = 'acrbrk330${suffix}'
var placeholderImage = 'mcr.microsoft.com/k8se/quickstart:latest'
var webTargetPort = webImage == placeholderImage ? 80 : 8080
var tags = {
  session: 'BRK330'
  product: 'Contoso Travel Concierge'
  customer: 'Caldova'
}

resource foundry 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' existing = {
  name: foundryAccountName
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' existing = {
  parent: foundry
  name: projectName
}

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'log-brk330-${suffix}'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-brk330-${suffix}'
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    IngestionMode: 'LogAnalytics'
  }
}

resource registry 'Microsoft.ContainerRegistry/registries@2025-11-01' = {
  name: registryName
  location: location
  tags: tags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
    anonymousPullEnabled: false
    roleAssignmentMode: 'LegacyRegistryPermissions'
  }
}

resource projectInsightsConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-04-01-preview' = {
  parent: project
  name: 'ApplicationInsights'
  properties: {
    category: 'AppInsights'
    authType: 'ApiKey'
    isSharedToAll: true
    target: appInsights.id
    credentials: {
      key: appInsights.properties.ConnectionString
    }
    metadata: {
      ApiType: 'AppInsights'
      ResourceId: appInsights.id
      ApplicationInsightsConnectionString: appInsights.properties.ConnectionString
      InstrumentationKey: appInsights.properties.InstrumentationKey
    }
  }
}

resource webIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-brk330-web-${suffix}'
  location: location
  tags: tags
}

resource webRegistryReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: registry
  name: guid(registry.id, webIdentity.id, acrPullRoleId)
  properties: {
    principalId: webIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleId)
  }
}

resource projectFoundryUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: foundry
  name: guid(foundry.id, project.id, foundryUserRoleId)
  properties: {
    principalId: project.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', foundryUserRoleId)
  }
}

resource webAgentConsumer 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: project
  name: guid(project.id, webIdentity.id, foundryAgentConsumerRoleId)
  properties: {
    principalId: webIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', foundryAgentConsumerRoleId)
  }
}

resource webFoundryUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: foundry
  name: guid(foundry.id, webIdentity.id, foundryUserRoleId)
  properties: {
    principalId: webIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', foundryUserRoleId)
  }
}

resource deploymentPrincipalProjectManager 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: foundry
  name: guid(foundry.id, principalId, foundryProjectManagerRoleId)
  properties: {
    principalId: principalId
    principalType: 'User'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', foundryProjectManagerRoleId)
  }
}

resource webMetricsPublisher 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: appInsights
  name: guid(appInsights.id, webIdentity.id, monitoringMetricsPublisherRoleId)
  properties: {
    principalId: webIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', monitoringMetricsPublisherRoleId)
  }
}

resource deploymentPrincipalInsightsReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: appInsights
  name: guid(appInsights.id, principalId, monitoringReaderRoleId)
  properties: {
    principalId: principalId
    principalType: 'User'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', monitoringReaderRoleId)
  }
}

resource projectInsightsReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: appInsights
  name: guid(appInsights.id, project.id, monitoringReaderRoleId)
  properties: {
    principalId: project.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', monitoringReaderRoleId)
  }
}

resource accountInsightsReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: appInsights
  name: guid(appInsights.id, foundry.id, monitoringReaderRoleId)
  properties: {
    principalId: foundry.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', monitoringReaderRoleId)
  }
}

resource hostedAgentInsightsReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(hostedAgentInstancePrincipalId)) {
  scope: appInsights
  name: guid(appInsights.id, hostedAgentInstancePrincipalId, monitoringReaderRoleId)
  properties: {
    principalId: hostedAgentInstancePrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', monitoringReaderRoleId)
  }
}

resource hostedAgentMetricsPublisher 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(hostedAgentInstancePrincipalId)) {
  scope: appInsights
  name: guid(appInsights.id, hostedAgentInstancePrincipalId, monitoringMetricsPublisherRoleId)
  properties: {
    principalId: hostedAgentInstancePrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', monitoringMetricsPublisherRoleId)
  }
}

resource containerEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: 'cae-brk330-${suffix}'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

resource web 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'contoso-travel-web'
  location: location
  dependsOn: [
    webRegistryReader
  ]
  tags: union(tags, {
    'azd-service-name': 'web'
  })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${webIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: webTargetPort
        allowInsecure: false
        transport: 'auto'
      }
      registries: configureRegistry ? [
        {
          server: registry.properties.loginServer
          identity: webIdentity.id
        }
      ] : []
    }
    template: {
      containers: [
        {
          name: 'web'
          image: webImage
          resources: {
            cpu: json('0.5')
            memory: '1.0Gi'
          }
          env: [
            { name: 'AZURE_CLIENT_ID', value: webIdentity.properties.clientId }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsights.properties.ConnectionString }
            { name: 'AZURE_AI_PROJECT_ENDPOINT', value: 'https://${foundry.name}.services.ai.azure.com/api/projects/${project.name}' }
            { name: 'CONTOSO_AGENT_NAME', value: 'contoso-travel' }
            { name: 'CONTOSO_CONFIGURATION', value: contosoConfiguration }
            { name: 'CONTOSO_FIXTURES_DIR', value: '/app/data/fixtures' }
            { name: 'CONTOSO_MODEL_DEPLOYMENT', value: contosoModelDeployment }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 2
      }
    }
  }
}

output APPLICATIONINSIGHTS_CONNECTION_STRING string = appInsights.properties.ConnectionString
output AZURE_CONTAINER_APPS_ENV_NAME string = containerEnvironment.name
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = registry.properties.loginServer
output AZURE_CONTAINER_REGISTRY_NAME string = registry.name
output AZURE_MONITOR_APP_INSIGHTS_NAME string = appInsights.name
output AZURE_MONITOR_LOG_ANALYTICS_NAME string = logAnalytics.name
output WEB_MANAGED_IDENTITY_CLIENT_ID string = webIdentity.properties.clientId
output WEB_MANAGED_IDENTITY_RESOURCE_ID string = webIdentity.id
output WEB_URL string = 'https://${web.properties.configuration.ingress.fqdn}'
