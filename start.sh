#!/bin/bash
# Script de démarrage pour le Scanner 3D
# Usage: ./start.sh [web|test|calibrate]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}    Scanner 3D - BTT Pi v1.2${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Erreur: Python3 n'est pas installé${NC}"
    exit 1
fi

# Vérifier les dépendances
echo -e "${YELLOW}Vérification des dépendances...${NC}"
python3 -c "import cv2" 2>/dev/null || {
    echo -e "${RED}opencv-python non installé. Installation...${NC}"
    pip3 install opencv-python
}

python3 -c "import flask" 2>/dev/null || {
    echo -e "${RED}Flask non installé. Installation...${NC}"
    pip3 install flask
}

python3 -c "import RPi.GPIO" 2>/dev/null || {
    echo -e "${YELLOW}RPi.GPIO non disponible (normal si ce n'est pas sur un Pi)${NC}"
}

echo -e "${GREEN}Dépendances OK${NC}"
echo ""

# Mode de démarrage
MODE="${1:-web}"

case $MODE in
    web|serveur)
        echo -e "${GREEN}Démarrage du serveur web...${NC}"
        echo -e "${YELLOW}Interface accessible sur http://$(hostname -I | awk '{print $1}'):5000${NC}"
        echo ""
        python3 web_app.py
        ;;
    test|tester)
        echo -e "${GREEN}Mode test - Scanner 3D${NC}"
        echo ""
        python3 scanner.py
        ;;
    calibrate|calibration)
        echo -e "${GREEN}Calibration des moteurs...${NC}"
        python3 -c "
from scanner import Scanner3D
s = Scanner3D()
s.calibrate()
s.cleanup()
"
        ;;
    preview|apercu)
        echo -e "${GREEN}Aperçu caméra (5 secondes)...${NC}"
        python3 -c "
from camera import WebcamCapture
cam = WebcamCapture()
cam.preview(duration=5)
"
        ;;
    *)
        echo -e "${YELLOW}Usage: $0 [web|test|calibrate|preview]${NC}"
        echo ""
        echo "Modes disponibles:"
        echo "  web        - Lance le serveur web (défaut)"
        echo "  test       - Mode test interactif"
        echo "  calibrate  - Calibration des moteurs"
        echo "  preview    - Aperçu caméra"
        exit 1
        ;;
esac
