// Contoso Travel Concierge — supplemental infrastructure
//
// The Foundry azd provider (declared in azure.yaml as
// `infra: provider: microsoft.foundry`) provisions the AI Services account,
// Foundry project, and model deployments. It does not create App Insights,
// wire it to the project, or provide the FastAPI web app hosting. This
// template covers the rest so a fresh `azd up` reproduces the full setup.
//
// Deployed by the `postprovision` hook in azure.yaml.

targetScope = 'resourceGroup'

@description('Sweden Central per spec.')
param location string = resourceGroup().location

@description('Foundry AI Services account name (provisioned by the Foundry provider).')
param foundryAccountName string

@description('Foundry project name (provisioned by the Foundry provider).')
param projectName string

@description('Environment identifier (short, unique-ish).')
param environmentName string

@description('Signed-in user object id (for local invoke/portal RBAC).')
param principalId string = ''

@description('Container image for the FastAPI web app. Overridden by azd deploy after first push.')
param webImage string = 'mcr.microsoft.com/k8se/quickstart:latest'

var suffix = toLower(uniqueString(subscription().id, resourceGroup().id, environmentName))
var logAnalyticsName = 'log-brk330-${suffix}'
var appInsightsName  = 'appi-brk330-${suffix}'
var caeName          = 'cae-brk330-${suffix}'
var acrName          = 'acrbrk330${suffix}'
var webName          = 'contoso-web'
var webIdentityName  = 'id-web-${suffix}'

var tags = {
  session: 'BRK330'
  product: 'Contoso Travel Concierge'
  customer: 'Caldova'
  variant: 'baseline'
}

// -------- Existing resources (managed by the Foundry provider) --------

resource foundry 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' existing = {
  name: foundryAccountName
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' existing = {
  parent: foundry
  name: projectName
}

// -------- Monitoring --------

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
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
  name: appInsightsName
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    Flow_Type: 'Bluefield'
    Request_Source: 'rest'
    WorkspaceResourceId: logAnalytics.id
    IngestionMode: 'LogAnalytics'
  }
}

// Foundry project connection to App Insights (so Foundry Insights preview
// and evaluation trace correlation can use it).
resource projectInsightsConnection 'Microsoft.CognitiveServices/accounts/projects/connections@2025-04-01-preview' = {
  parent: project
  name: 'ApplicationInsights'
  properties: {
    category: 'AppInsights'
    authType: 'ApiKey'
    // Shared at project scope so the Foundry Insights preview scan and the
    // evaluation runners can both read the connection without per-user grants.
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

// -------- RBAC (least-privilege, per spec §Observability) --------
// Foundry project managed identity needs Monitoring Reader on App Insights
// so the Insights preview can pull evaluated-trace evidence. The hosted-agent
// instance identity also needs Monitoring Reader (Insights preview scans it
// as a data source) and Monitoring Metrics Publisher (so the SDK inside the
// container can actually push trace telemetry).

var monitoringReader           = '43d0d8ad-25c7-4714-9337-8ba259a9fe05'
var monitoringMetricsPublisher = '3913510d-42f4-4e42-8a64-420c390055eb'
var acrPull                    = '7f951dda-4ed3-4680-a7ca-43fe172d538d'

// Hosted-agent instance identity (managed by the Foundry provider). Its
// principal id is exported from azd as AGENT_CONTOSO_TRAVEL_INSTANCE_IDENTITY_PRINCIPAL_ID.
@description('Object id of the hosted-agent instance managed identity (from azd env).')
param hostedAgentInstancePrincipalId string = ''

resource projectMonitoringReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: appInsights
  name: guid(appInsights.id, project.id, monitoringReader)
  properties: {
    principalId: project.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', monitoringReader)
  }
}

resource accountMonitoringReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: appInsights
  name: guid(appInsights.id, foundry.id, monitoringReader)
  properties: {
    principalId: foundry.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', monitoringReader)
  }
}

// Project managed identity also needs Foundry data-plane roles on the parent
// AI account so the Monitor tab (and Insights preview) can call the account
// APIs to enumerate deployments, judge models, and evaluators. Without these
// the portal surfaces "Setup incomplete: The project managed identity needs
// access to the Foundry account".
resource projectAccountFoundryUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: foundry
  name: guid(foundry.id, project.id, foundryUser)
  properties: {
    principalId: project.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', foundryUser)
  }
}

resource projectAccountCogUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: foundry
  name: guid(foundry.id, project.id, cognitiveServicesUser)
  properties: {
    principalId: project.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesUser)
  }
}

resource projectAccountOpenAIUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: foundry
  name: guid(foundry.id, project.id, cognitiveServicesOpenAIUser)
  properties: {
    principalId: project.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesOpenAIUser)
  }
}

// Hosted-agent instance identity — only granted when azd exported its
// principal id (first `azd deploy contoso-travel` sets it). Second `azd up`
// picks it up. Idempotent.
resource hostedAgentMetricsPublisher 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(hostedAgentInstancePrincipalId)) {
  scope: appInsights
  name: guid(appInsights.id, 'hosted-agent-metrics', hostedAgentInstancePrincipalId)
  properties: {
    principalId: hostedAgentInstancePrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', monitoringMetricsPublisher)
  }
}

resource hostedAgentMonitoringReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(hostedAgentInstancePrincipalId)) {
  scope: appInsights
  name: guid(appInsights.id, 'hosted-agent-reader', hostedAgentInstancePrincipalId)
  properties: {
    principalId: hostedAgentInstancePrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', monitoringReader)
  }
}

// -------- Web app hosting (Azure Container Apps) --------

resource acr 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: acrName
  location: location
  tags: tags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
    anonymousPullEnabled: false
  }
}

resource webIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: webIdentityName
  location: location
  tags: tags
}

resource webAcrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: acr
  name: guid(acr.id, webIdentity.id, acrPull)
  properties: {
    principalId: webIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPull)
  }
}

resource webInsightsMetricsPublisher 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: appInsights
  name: guid(appInsights.id, webIdentity.id, monitoringMetricsPublisher)
  properties: {
    principalId: webIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', monitoringMetricsPublisher)
  }
}

// Give the web MI access to invoke Foundry (matches spec's live end-to-end story).
var cognitiveServicesOpenAIUser = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
var cognitiveServicesUser       = 'a97b65f3-24c7-4388-baec-2e87135dc908'
// "Foundry User" (aka "Azure AI User") — the role the CLI signed-in user
// receives at subscription scope. Same role guid the account/agent-scope grants
// above use.
var foundryUser                 = '53ca6127-db72-4b80-b1b0-d745d6d5456d'

resource webFoundryOpenAIUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: foundry
  name: guid(foundry.id, webIdentity.id, cognitiveServicesOpenAIUser)
  properties: {
    principalId: webIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesOpenAIUser)
  }
}

resource webFoundryCogUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: foundry
  name: guid(foundry.id, webIdentity.id, cognitiveServicesUser)
  properties: {
    principalId: webIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesUser)
  }
}

// Project-scope grants — the Foundry hosted-agent Responses endpoint enforces
// permission at the project scope, so account-scope grants are not sufficient
// on their own.
resource webProjectCogUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: project
  name: guid(project.id, webIdentity.id, cognitiveServicesUser)
  properties: {
    principalId: webIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesUser)
  }
}

resource webProjectOpenAIUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: project
  name: guid(project.id, webIdentity.id, cognitiveServicesOpenAIUser)
  properties: {
    principalId: webIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesOpenAIUser)
  }
}

resource webProjectFoundryUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: project
  name: guid(project.id, webIdentity.id, foundryUser)
  properties: {
    principalId: webIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', foundryUser)
  }
}

resource cae 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: caeName
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
  name: webName
  location: location
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
    managedEnvironmentId: cae.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8080
        allowInsecure: false
        transport: 'auto'
      }
      registries: [
        {
          server: acr.properties.loginServer
          identity: webIdentity.id
        }
      ]
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
            { name: 'AZURE_CLIENT_ID',                       value: webIdentity.properties.clientId }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsights.properties.ConnectionString }
            { name: 'AZURE_AI_PROJECT_ENDPOINT',             value: 'https://${foundry.name}.services.ai.azure.com/api/projects/${project.name}' }
            { name: 'CONTOSO_MODEL_DEPLOYMENT',              value: 'gpt-5' }
            { name: 'CONTOSO_VARIANT',                       value: 'baseline' }
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

// -------- Outputs (postprovision hook writes these back into azd env) --------

output APPLICATIONINSIGHTS_CONNECTION_STRING string = appInsights.properties.ConnectionString
output AZURE_MONITOR_APP_INSIGHTS_NAME string = appInsights.name
output AZURE_MONITOR_LOG_ANALYTICS_NAME string = logAnalytics.name
output AZURE_CONTAINER_APPS_ENV_NAME string = cae.name
output AZURE_CONTAINER_REGISTRY_NAME string = acr.name
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = acr.properties.loginServer
output WEB_URL string = 'https://${web.properties.configuration.ingress.fqdn}'
output WEB_MANAGED_IDENTITY_CLIENT_ID string = webIdentity.properties.clientId
output WEB_MANAGED_IDENTITY_RESOURCE_ID string = webIdentity.id
