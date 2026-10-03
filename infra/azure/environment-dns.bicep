param prefix string
param domain string
param address string
param vnetId string
resource zone 'Microsoft.Network/privateDnsZones@2024-06-01' = { name: domain, location: 'global' }
resource link 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = { parent: zone, name: '${prefix}-apps', location: 'global', properties: { virtualNetwork: { id: vnetId }, registrationEnabled: false } }
resource wildcard 'Microsoft.Network/privateDnsZones/A@2024-06-01' = { parent: zone, name: '*', properties: { ttl: 300, aRecords: [{ ipv4Address: address }] } }
