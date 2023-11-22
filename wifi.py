import wifi

# scan for available WiFi networks
wifi_scanner = wifi.Cell.all('wlan0')
available_networks = [cell.ssid for cell in wifi_scanner]

# print available networks
print(f"Available Networks: {available_networks}")

# connect to a WiFi network
network_ssid = "iPhone de Henrique"
network_pass = "senhadohenrique"

for cell in wifi_scanner:
	if cell.ssid == network_ssid:
		b = 2
		scheme = wifi.Scheme.for_cell('wlan0', cell.ssid, cell, network_pass)
		scheme.save()
		scheme.activate()
		print(f"Coneccted to network: {network_ssid}")
		break
	
else:
	print(f"Unable to find network: {network_ssid}")