// Deploy only after the approved foundation, secrets, DB roles and explicit migration.
param prefix string
param location string
param environmentId string
param registryId string
param registryHost string
param vaultId string
param vaultUri string
param blobContainerId string
@description('Immutable sha256 image reference, not a mutable tag.')
param apiImage string
param webImage string
param approvedWebOrigin string
param entraTenantId string
param webClientId string
param apiAudience string
param apiScope string
@minValue(1)
@maxValue(8)
param maxReplicas int
var serverSecrets = ['ap-database-url','ap-enterprise-config']
var serverEnv = [
  { name: 'AP_ENVIRONMENT', value: 'enterprise' }
  { name: 'AP_DATABASE_URL', secretRef: 'ap-database-url' }
  { name: 'AP_CONFIG_JSON', secretRef: 'ap-enterprise-config' }
]
module api 'app.bicep' = { name: 'api', params: { name: '${prefix}-api', location: location, environmentId: environmentId, image: apiImage, registryId: registryId, registryHost: registryHost, vaultId: vaultId, vaultUri: vaultUri, blobContainerId: blobContainerId, service: 'api', env: serverEnv, secretNames: serverSecrets, maxReplicas: maxReplicas } }
module worker 'app.bicep' = { name: 'worker', params: { name: '${prefix}-worker', location: location, environmentId: environmentId, image: apiImage, registryId: registryId, registryHost: registryHost, vaultId: vaultId, vaultUri: vaultUri, blobContainerId: blobContainerId, service: 'worker', env: serverEnv, secretNames: serverSecrets, command: ['python','-m','app.services.worker'], maxReplicas: 1 } }
module web 'app.bicep' = { name: 'web', params: { name: '${prefix}-web', location: location, environmentId: environmentId, image: webImage, registryId: registryId, registryHost: registryHost, vaultId: vaultId, vaultUri: vaultUri, blobContainerId: blobContainerId, service: 'web', secretNames: ['ap-web-client-secret'], maxReplicas: maxReplicas, env: [{ name: 'AP_ENVIRONMENT', value: 'enterprise' },{ name: 'AP_API_ORIGIN', value: 'https://${api.outputs.fqdn}' },{ name: 'AP_WEB_ORIGIN', value: approvedWebOrigin }] } }
resource webApp 'Microsoft.App/containerApps@2025-01-01' existing = { name: '${prefix}-web' }
resource authentication 'Microsoft.App/containerApps/authConfigs@2025-01-01' = {
  parent: webApp
  name: 'current'
  properties: {
    platform: { enabled: true }
    globalValidation: { unauthenticatedClientAction: 'RedirectToLoginPage', redirectToProvider: 'azureActiveDirectory', excludedPaths: ['/health'] }
    identityProviders: { azureActiveDirectory: { enabled: true, registration: { clientId: webClientId, clientSecretSettingName: 'ap-web-client-secret', openIdIssuer: '${environment().authentication.loginEndpoint}${entraTenantId}/v2.0' }, validation: { allowedAudiences: [webClientId,apiAudience] }, login: { loginParameters: ['scope=openid profile email offline_access ${apiScope}'] } } }
    login: { tokenStore: { enabled: true } }
    httpSettings: { requireHttps: true }
  }
  dependsOn: [web]
}
output webFqdn string = web.outputs.fqdn
output apiFqdn string = api.outputs.fqdn
output workerName string = worker.outputs.name
