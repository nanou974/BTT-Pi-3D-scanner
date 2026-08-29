# Scanner 3D avec BTT Pi v1.2 et Webcam

Un scanner 3D basé sur la photographie (photogrammétrie), utilisant un BTT Pi v1.2 comme contrôleur principal, des moteurs NEMA17 pour le plateau tournant et le bras caméra, et une webcam USB pour la capture d'images.

Inspiré par le projet [OpenScan](https://openscan.eu/) - Scanner 3D open source.

## Fonctionnalités

- **Plateau tournant motorisé** : Rotation précise de l'objet à 360°
- **Bras caméra motorisé** : Déplacement vertical pour captures sous différents angles
- **Capture automatisée** : Séquence de scan complète avec peu d'intervention
- **Interface web** : Contrôle à distance depuis n'importe quel navigateur
- **Webcam USB** : Compatible avec la plupart des webcams USB
- **Éclairage continu** : Trust Spotlight Pro modifiée (LED permanent, potentiomètre retiré)
- **Scan par couches** : Plusieurs positions verticales du bras pour une meilleure couverture 3D

## Matériel nécessaire

### Électronique
| Composant | Quantité | Notes |
|-----------|----------|-------|
| BTT Pi v1.2 | 1 | Contrôleur principal (Allwinner H616, 1GB RAM) |
| Arduino Uno | 1 | Contrôleur moteurs (via USB depuis le BTT Pi) |
| CNC Shield V3 | 1 | Shield Arduino pour A4988 (monté sur l'Arduino Uno) |
| A4988 | 2 | Drivers pour moteurs pas à pas (montés sur le CNC Shield) |
| NEMA17 | 2 | Moteurs pas à pas (>13Ncm pour plateau, >40Ncm recommandé) |
| Logitech C300 | 1 | Webcam pour la capture d'images (sans LED) |
| Trust Spotlight Pro | 1 | Éclairage continu (modifiée: potentiomètre LED retiré, éclairage permanent) |
| Alimentation 12V-24V | 1 | Pour les moteurs (bornier du CNC Shield) |
| Micro SD Card | 1 | >16GB, classe 10 |

### Impression 3D
- Pièces pour le plateau tournant
- Pièces pour le bras caméra
- Support pour la webcam
- Structure/frame du scanner

## Architecture

```
BTT Pi v1.2 (Armbian, Python)
    │
    ├── USB ──→ Arduino Uno (CNC Shield V3, A4988)
    │               ├── X axis → NEMA17 Plateau
    │               └── Y axis → NEMA17 Bras Caméra
    │
    ├── USB ──→ Logitech C300 (capture images)
    └── USB ──→ Trust Spotlight Pro (éclairage continu)
```

## Système d'exploitation recommandé

### Armbian Minimal/CLI (Recommandé)

**C'est le meilleur choix pour ce projet.** Téléchargez l'image depuis : [BigTreeTech CB1 Releases](https://github.com/bigtreetech/CB1/releases)

| Caractéristique | Détail |
|-----------------|--------|
| **Version** | Armbian Minimal/CLI (pas de bureau graphique) |
| **Avantages** | Léger, accès GPIO complet, pas de Klipper qui prend le contrôle |
| **Accès** | SSH (Putty, MobaXterm, ou terminal) |
| **Login** | `root` / `root` (puis créer un user lors de la 1ère connexion) |

**Pourquoi Armbian Minimal et pas Klipper ?**
- **Klipper** est conçu pour les imprimantes 3D et monopolise certaines ressources GPIO
- **Armbian Minimal** est une base Linux propre, idéale pour du code Python custom
- Pas de surcharge inutile - le scanner n'a pas besoin de Klipper
- Accès complet au GPIO pour le contrôle des drivers A4988

### Flasher l'image

1. Téléchargez l'image Armbian Minimal depuis [CB1 Releases](https://github.com/bigtreetech/CB1/releases)
2. Utilisez [Raspberry Pi Imager](https://www.raspberrypi.com/software/) ou [balenaEtcher](https://etcher.balena.io/) pour flasher la carte SD
3. Avant de booter, éditez le fichier `system.cfg` sur la partition BOOT :
   ```bash
   # Activer le WiFi (optionnel mais recommandé)
   WIFI_SSID="Votre_SSID"
   WIFI_PASSWD="Votre_Mot_de_passe"
   
   # Hostname (optionnel)
   hostname="scanner3d"
   ```

### Alternative : Image Klipper

Si vous avez déjà Klipper installé, vous pouvez l'utiliser mais ce n'est pas optimal pour ce projet. Les identifiants par défaut sont :
- Login : `biqu` / Mot de passe : `biqu`
- Root : `root` / Mot de passe : `root`

## Installation

### 1. Connexion au BTT Pi

```bash
# En SSH (remplacez par l'IP de votre BTT Pi)
ssh root@<IP_DU_BTT_PI>

# Ou via hostname si mDNS est configuré
ssh root@scanner3d.local
```

### 2. Installer les dépendances

```bash
# Mettre à jour le système
apt update && apt upgrade -y

# Installer Python3 et pip
apt install -y python3 python3-pip python3-venv python3-opencv libgl1 libglib2.0-0 git

# Cloner le projet
cd /opt
git clone https://github.com/nanou974/BTT-Pi-3D-scanner.git
cd BTT-Pi-3D-scanner

# Créer un environnement virtuel (requis avec Python 3.13+)
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances Python
pip install -r requirements.txt
```

### 3. Flasher l'Arduino Uno

Installer l'Arduino IDE ou `arduino-cli`, puis uploader le firmware :

```bash
# Avec Arduino IDE : ouvrir arduino_firmware/scanner3d.ino
# Sélectionner "Arduino Uno" comme carte
# Cliquer "Upload"

# Ou avec arduino-cli :
arduino-cli compile --fqbn arduino:avr:uno arduino_firmware/scanner3d.ino
arduino-cli upload -p /dev/ttyUSB0 --fqbn arduino:avr:uno arduino_firmware/scanner3d.ino
```

Le port série varie selon le système :
- **Linux (Armbian)** : `/dev/ttyUSB0` ou `/dev/ttyACM0`
- **Windows** : `COM3`, `COM4`, etc.

### 4. Connecter le matériel

```
BTT Pi v1.2          Arduino Uno + CNC Shield
─────────────        ────────────────────────
USB ──────────────→  USB (alimentation + série)

CNC Shield           NEMA17
────────────        ───────
X.STEP/DIR ──────→  Moteur Plateau
Y.STEP/DIR ──────→  Moteur Bras Caméra
12-36V ───────────→  Alimentation moteurs

Câbler les moteurs 4 fils sur les borniers du CNC Shield (X et Y).
```

### 5. Lancer le scanner

```bash
cd /opt/BTT-Pi-3D-scanner
source venv/bin/activate

# Mode terminal (test)
python3 scanner.py

# Mode interface web (accessible depuis un navigateur)
python3 web_app.py
```

### 6. Accéder à l'interface web

Depuis un navigateur sur le même réseau :
```
http://<IP_DU_BTT_PI>:5000
```

## Utilisation

### Interface Web

1. Ouvrir un navigateur sur `http://<IP_DU_BTT_PI>:5000`
2. Configurer les paramètres du scan (photos par rotation, positions verticales)
3. Cliquer sur "Démarrer le scan"
4. Suivre la progression dans le journal

### Mode Terminal

```python
from scanner import Scanner3D

scanner = Scanner3D()

# Scan rapide (36 photos, 3 positions verticales)
scanner.quick_scan(photos=36, arm_steps=3)

# Ou scan personnalisé
scanner.start_scan(photos_per_rotation=36, arm_positions=5)
scanner.execute_scan()
```

### Calibration

```bash
python3 -c "
from scanner import Scanner3D
s = Scanner3D()
s.calibrate()
s.cleanup()
"
```

## Structure du projet

```
BTT-Pi-3D-scanner/
├── config.py              # Configuration (Arduino, moteurs, webcam)
├── stepper.py             # Contrôle moteurs via Arduino + CNC Shield
├── camera.py              # Capture webcam USB (OpenCV)
├── scanner.py             # Scanner principal (coordination)
├── web_app.py             # Interface web Flask
├── test_hardware.py       # Diagnostic matériel
├── requirements.txt       # Dépendances Python
├── wiring.md              # Schéma de câblage
├── start.sh               # Script de démarrage rapide
├── .gitignore             # Fichiers ignorés par Git
├── README.md              # Cette documentation
└── arduino_firmware/      # Firmware Arduino
    ├── scanner3d.ino      # Firmware principal
    └── README.md          # Documentation Arduino
```

## Personnalisation

### Changer le nombre de photos

Dans `config.py` :
```python
SCAN_SETTINGS = {
    "photos_per_rotation": 72,  # Plus de photos = meilleure qualité
    "arm_positions": 10,        # Plus de positions = meilleure couverture
}
```

### Utiliser une autre webcam

```python
WEBCAM = {
    "device_id": 1,                    # Deuxième webcam détectée
    "resolution": (1280, 720),         # Résolution plus faible = plus rapide
}
```

### Lancer au démarrage du système

Pour lancer le scanner automatiquement au boot :

```bash
# Créer un service systemd
cat > /etc/systemd/system/scanner3d.service << 'EOF'
[Unit]
Description=Scanner 3D Web Interface
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/BTT-Pi-3D-scanner
ExecStart=/opt/BTT-Pi-3D-scanner/venv/bin/python /opt/BTT-Pi-3D-scanner/web_app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Activer le service
systemctl daemon-reload
systemctl enable scanner3d
systemctl start scanner3d
```

## Dépannage

### La webcam ne fonctionne pas
```bash
ls /dev/video*
python3 -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

### L'Arduino n'est pas détectée
```bash
# Vérifier les ports USB série
ls /dev/ttyUSB* /dev/ttyACM*

# Permissions
sudo usermod -a -G dialout $USER
```

### Les moteurs ne bougent pas
- Vérifier que l'Arduino est alimentée (USB ou 12V)
- Vérifier que les drivers A4988 sont bien montés sur le CNC Shield
- Vérifier l'alimentation 12-36V sur le bornier bleu du shield
- Vérifier les microstepping (jumpers MS1/MS2/MS3)

### Le serveur web ne démarre pas
```bash
cd /opt/BTT-Pi-3D-scanner
source venv/bin/activate
pip install flask
python3 web_app.py
```

## Licence

Projet open source - Utilisez librement pour vos projets personnels.

## Crédits

- Inspiré par [OpenScan](https://openscan.eu/) - Scanner 3D open source
- [BTT Pi v1.2](https://github.com/bigtreetech/BTT-Pi) - BigTreeTech
- [Armbian](https://www.armbian.com/) - Système d'exploitation pour ARM
- [CNC Shield V3](https://github.com/grbl-Mega/blob/master/Grbl%20v1.1/grbl_v1.1g_eeprom_loader/README.md) - Arduino CNC Shield
- Interface web avec [Flask](https://flask.palletsprojects.com/)
- Capture vidéo avec [OpenCV](https://opencv.org/)
