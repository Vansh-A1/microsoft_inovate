targetScope = 'resourceGroup'
@description('Approved short environment name; no subscription/region is guessed.')
@minLength(3)
@maxLength(11)
param prefix string
param location string
param vnetCidr string
param appsSubnetCidr string
param databaseSubnetCidr string
param endpointsSubnetCidr string
param databaseAdministrator string
@secure()
param databaseAdministratorPassword string
@minValue(7)
@maxValue(35)
param databaseBackupDays int
@minValue(1)
@maxValue(365)
param blobRecoveryDays int
@minValue(30)
@maxValue(730)
param logRetentionDays int
param databaseSku string
param databaseTier string
@minValue(32)
param databaseStorageGiB int
param highAvailabilityMode string
var suffix = uniqueString(resourceGroup().id)
var storageName = '${prefix}${suffix}'
var registryName = '${prefix}${suffix}acr'
var vaultName = '${prefix}-${suffix}-kv'

resource network 'Microsoft.Network/virtualNetworks@2024-05-01' = {
  name: '${prefix}-network'
  location: location
  properties: {
    addressSpace: { addressPrefixes: [vnetCidr] }
    subnets: [
      { name: 'apps', properties: { addressPrefix: appsSubnetCidr, delegations: [{ name: 'apps', properties: { serviceName: 'Microsoft.App/environments' } }] } }
      { name: 'database', properties: { addressPrefix: databaseSubnetCidr, delegations: [{ name: 'database', properties: { serviceName: 'Microsoft.DBforPostgreSQL/flexibleServers' } }] } }
      { name: 'endpoints', properties: { addressPrefix: endpointsSubnetCidr, privateEndpointNetworkPolicies: 'Disabled' } }
    ]
  }
}
var appsSubnet = '${network.id}/subnets/apps'
var databaseSubnet = '${network.id}/subnets/database'
var endpointsSubnet = '${network.id}/subnets/endpoints'
resource databaseZone 'Microsoft.Network/privateDnsZones@2024-06-01' = {
  name: '${prefix}.postgres.database.azure.com'
  location: 'global'
}
resource databaseLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = {
  parent: databaseZone
  name: '${prefix}-database'
  location: 'global'
  properties: { virtualNetwork: { id: network.id }, registrationEnabled: false }
}
resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' = {
  name: '${prefix}-${suffix}-pg'
  location: location
  sku: { name: databaseSku, tier: databaseTier }
  properties: {
    version: '16'
    administratorLogin: databaseAdministrator
    administratorLoginPassword: databaseAdministratorPassword
    storage: { storageSizeGB: databaseStorageGiB }
    backup: { backupRetentionDays: databaseBackupDays, geoRedundantBackup: 'Disabled' }
    highAvailability: { mode: highAvailabilityMode }
    network: { delegatedSubnetResourceId: databaseSubnet, privateDnsZoneArmResourceId: databaseZone.id, publicNetworkAccess: 'Disabled' }
  }
  dependsOn: [databaseLink]
}
resource db 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2024-08-01' = {
  parent: postgres
  name: 'ap'
  properties: { charset: 'UTF8', collation: 'en_US.utf8' }
}
resource objects 'Microsoft.Storage/storageAccounts@2024-01-01' = {
  name: storageName
  location: location
  kind: 'StorageV2'
  sku: { name: 'Standard_ZRS' }
  properties: { publicNetworkAccess: 'Disabled', allowBlobPublicAccess: false, allowSharedKeyAccess: false, minimumTlsVersion: 'TLS1_2', supportsHttpsTrafficOnly: true, networkAcls: { defaultAction: 'Deny', bypass: 'None' } }
}
resource blob 'Microsoft.Storage/storageAccounts/blobServices@2024-01-01' = {
  parent: objects
  name: 'default'
  properties: {
    isVersioningEnabled: true
    deleteRetentionPolicy: { enabled: true, days: blobRecoveryDays }
    containerDeleteRetentionPolicy: { enabled: true, days: blobRecoveryDays }
  }
}
resource originals 'Microsoft.Storage/storageAccounts/blobServices/containers@2024-01-01' = {
  parent: blob
  name: 'documents'
  properties: { publicAccess: 'None' }
}
resource vault 'Microsoft.KeyVault/vaults@2024-11-01' = {
  name: vaultName
  location: location
  properties: { tenantId: tenant().tenantId, sku: { family: 'A', name: 'standard' }, enableRbacAuthorization: true, enablePurgeProtection: true, enableSoftDelete: true, publicNetworkAccess: 'Disabled', networkAcls: { defaultAction: 'Deny', bypass: 'None' } }
}
resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: registryName
  location: location
  sku: { name: 'Premium' }
  properties: { adminUserEnabled: false, publicNetworkAccess: 'Disabled', policies: { trustPolicy: { type: 'Notary', status: 'disabled' } } }
}
module blobEndpoint 'private-endpoint.bicep' = { name: 'blob-private', params: { name: '${prefix}-blob', location: location, subnetId: endpointsSubnet, serviceId: objects.id, groupId: 'blob', dnsZone: 'privatelink.blob.${environment().suffixes.storage}', vnetId: network.id } }
module vaultEndpoint 'private-endpoint.bicep' = { name: 'vault-private', params: { name: '${prefix}-vault', location: location, subnetId: endpointsSubnet, serviceId: vault.id, groupId: 'vault', dnsZone: 'privatelink.vaultcore.azure.net', vnetId: network.id } }
module registryEndpoint 'private-endpoint.bicep' = { name: 'registry-private', params: { name: '${prefix}-registry', location: location, subnetId: endpointsSubnet, serviceId: registry.id, groupId: 'registry', dnsZone: 'privatelink.azurecr.io', vnetId: network.id } }
resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${prefix}-logs'
  location: location
  properties: { sku: { name: 'PerGB2018' }, retentionInDays: logRetentionDays, features: { enableLogAccessUsingOnlyResourcePermissions: true } }
}
resource controlEnvironment 'Microsoft.App/managedEnvironments@2025-01-01' = {
  name: '${prefix}-control'
  location: location
  properties: {
    vnetConfiguration: { infrastructureSubnetId: appsSubnet, internal: true }
    workloadProfiles: [{ name: 'Consumption', workloadProfileType: 'Consumption' }]
    appLogsConfiguration: { destination: 'log-analytics', logAnalyticsConfiguration: { customerId: logs.properties.customerId, sharedKey: logs.listKeys().primarySharedKey } }
  }
}
module environmentDns 'environment-dns.bicep' = { name: 'environment-dns', params: { prefix: prefix, domain: controlEnvironment.properties.defaultDomain, address: controlEnvironment.properties.staticIp, vnetId: network.id } }
output environmentId string = controlEnvironment.id
output environmentDomain string = controlEnvironment.properties.defaultDomain
output blobUrl string = objects.properties.primaryEndpoints.blob
output blobContainerId string = originals.id
output databaseHost string = postgres.properties.fullyQualifiedDomainName
output registryId string = registry.id
output registryHost string = registry.properties.loginServer
output vaultId string = vault.id
output vaultUri string = vault.properties.vaultUri
output logsId string = logs.id
