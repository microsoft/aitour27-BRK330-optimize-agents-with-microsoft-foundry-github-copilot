# Supplemental infrastructure

The Foundry azd provider (`infra: provider: microsoft.foundry` in
`azure.yaml`) provisions the AI Services account, Foundry project, and model
deployments (`gpt-5`, `gpt-4.1`, `model-router`).

`supplemental.bicep` covers everything else the spec requires:

- Log Analytics workspace + Application Insights
- Foundry project → App Insights **connection** (Foundry Insights preview
  and evaluation trace correlation)
- **RBAC** (least-privilege):
  - Project managed identity → *Monitoring Reader* on App Insights
  - Account managed identity → *Monitoring Reader* on App Insights
  - Web managed identity → *Monitoring Metrics Publisher* on App Insights,
    *AcrPull* on the container registry, and Foundry *Cognitive Services
    User* + *Cognitive Services OpenAI User* on the account
- Azure Container Registry
- User-assigned managed identity for the web app
- Container Apps environment
- `contoso-web` Container App (FastAPI experience; image swapped in by
  `azd deploy web` on the first push)

Deployed by the `postprovision` hook in `azure.yaml`, so a fresh
`azd up` reproduces the full setup end-to-end.
