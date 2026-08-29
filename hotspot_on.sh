#!/bin/bash
# Basculer en mode Hotspot (point d'accès WiFi)
# Le BTT Pi crée son propre réseau : Scanner3D

set -e

echo "[Network] Bascule en mode Hotspot..."

# Arrêter wpa_supplicant
sudo systemctl stop wpa_supplicant 2>/dev/null || true

# Configurer l'interface
sudo ip link set wlan0 up
sudo ip addr flush dev wlan0
sudo ip addr add 192.168.4.1/24 dev wlan0

# Démarrer le hotspot
sudo systemctl unmask hostapd
sudo systemctl start hostapd

# Démarrer le DHCP
sudo systemctl start dnsmasq

echo "[Network] Hotspot actif : Scanner3D"
echo "[Network] IP : 192.168.4.1"
echo "[Network] Interface : http://192.168.4.1:5000"
