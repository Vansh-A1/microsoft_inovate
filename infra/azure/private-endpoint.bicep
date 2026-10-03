param name string
param location string
param subnetId string
param serviceId string
param groupId string
param dnsZone string
param vnetId string
resource zone 'Microsoft.Network/privateDnsZones@2024-06-01' = {
  name: dnsZone
  location: 'global'
}
resource link 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = {
  parent: zone
  name: '${name}-link'
  location: 'global'
  properties: { virtualNetwork: { id: vnetId }, registrationEnabled: false }
}
resource endpoint 'Microsoft.Network/privateEndpoints@2024-05-01' = {
  name: name
  location: location
  properties: {
    subnet: { id: subnetId }
    privateLinkServiceConnections: [{ name: name, properties: { privateLinkServiceId: serviceId, groupIds: [groupId] } }]
  }
}
resource association 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2024-05-01' = {
  parent: endpoint
  name: 'default'
  properties: { privateDnsZoneConfigs: [{ name: 'service', properties: { privateDnsZoneId: zone.id } }] }
}
