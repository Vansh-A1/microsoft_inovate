param name string
param location string
param environmentId string
param image string
param registryId string
param registryHost string
param vaultId string
param vaultUri string
param blobContainerId string
@allowed(['api','worker','web'])
param service string
param env array
param secretNames array
param command array = []
@minValue(1)
@maxValue(8)
param maxReplicas int
resource managed 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = { name: '${name}-identity', location: location }
resource vault 'Microsoft.KeyVault/vaults@2024-11-01' existing = { name: last(split(vaultId,'/')) }
resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = { name: last(split(registryId,'/')) }
resource configuredSecret 'Microsoft.KeyVault/vaults/secrets@2024-11-01' existing = [for secret in secretNames: {
  parent: vault
  name: secret
}]
resource vaultRead 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for (secret,i) in secretNames: {
  scope: configuredSecret[i]
  name: guid(vault.id,managed.id,secret,'secrets-reader')
  properties: { principalId: managed.properties.principalId, principalType: 'ServicePrincipal', roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions','4633458b-17de-408a-b874-0445c86b69e6') }
}]
resource imageRead 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: registry
  name: guid(registry.id,managed.id,'image-reader')
  properties: { principalId: managed.properties.principalId, principalType: 'ServicePrincipal', roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions','7f951dda-4ed3-4680-a7ca-43fe172d538d') }
}
// Container-scoped data role; web receives no object permission.
resource account 'Microsoft.Storage/storageAccounts@2024-01-01' existing = { name: split(blobContainerId,'/')[8] }
resource blob 'Microsoft.Storage/storageAccounts/blobServices@2024-01-01' existing = { parent: account, name: 'default' }
resource container 'Microsoft.Storage/storageAccounts/blobServices/containers@2024-01-01' existing = { parent: blob, name: last(split(blobContainerId,'/')) }
resource objectWrite 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (service!='web') {
  scope: container
  name: guid(container.id,managed.id,'object-writer')
  properties: { principalId: managed.properties.principalId, principalType: 'ServicePrincipal', roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions','ba92f5b4-2d11-453d-a403-e96b0029c9fe') }
}
resource app 'Microsoft.App/containerApps@2025-01-01' = {
  name: name
  location: location
  identity: { type: 'UserAssigned', userAssignedIdentities: { '${managed.id}': {} } }
  properties: {
    managedEnvironmentId: environmentId
    workloadProfileName: 'Consumption'
    configuration: {
      activeRevisionsMode: 'Multiple'
      ingress: service=='worker'?null:{ external: service=='web', targetPort: service=='web'?3000:8000, allowInsecure: false, transport: 'auto', traffic: [{ latestRevision: true, weight: 100 }] }
      registries: [{ server: registryHost, identity: managed.id }]
      secrets: [for secret in secretNames: { name: secret, keyVaultUrl: '${vaultUri}secrets/${secret}', identity: managed.id }]
    }
    template: {
      containers: [{ name: service, image: image, command: command, env: concat(env,[{ name: 'AP_MANAGED_IDENTITY_CLIENT_ID', value: managed.properties.clientId }]), resources: { cpu: 1, memory: '2Gi' }, probes: service=='worker'?[]:[{ type: 'Readiness', httpGet: { path: service=='web'?'/health':'/api/v1/health/ready', port: service=='web'?3000:8000 }, initialDelaySeconds: 15, periodSeconds: 15, timeoutSeconds: 5 }] }]
      scale: { minReplicas: 1, maxReplicas: maxReplicas }
    }
  }
  dependsOn: [vaultRead,imageRead,objectWrite]
}
output name string = app.name
output identityClientId string = managed.properties.clientId
output fqdn string = service=='worker'?'':app.properties.configuration.ingress.fqdn
