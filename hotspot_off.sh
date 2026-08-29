#!/bin/bash
# Basculer en mode Normal (client WiFi)
# Se connecte au réseau WiFi configuré dans wpa_supplicant

set -e

echo "[Network] Bascule en mode Normal..."

# Arrêter le hotspot
sudo systemctl stop hostapd 2>/dev/null || true
sudo systemctl stop dnsmasq 2>/dev/null || true

# Redémarrer le client WiFi
sudo systemctl restart wpa_supplicant

echo "[Network] Mode client WiFi activé"
echo "[Network] Connexion au réseau..."
