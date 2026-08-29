# Scanner 3D avec BTT Pi v1.2 et Webcam

Un scanner 3D basé sur la photographie, utilisant un BTT Pi v1.2 comme contrôleur principal, des moteurs NEMA17 pour le plateau tournant et le bras caméra, et une webcam USB pour la capture d'images.

## Fonctionnalités

- **Plateau tournant motorisé** : Rotation précise de l'objet à 360°
- **Bras caméra motorisé** : Déplacement vertical pour captures sous différents angles
- **Capture automatisée** : Séquence de scan complète avec peu d'intervention
- **Interface web** : Contrôle à distance depuis n'importe quel navigateur
- **Webcam USB** : Compatible avec la plupart des webcams USB

## Matériel nécessaire

### Électronique
| Composant | Quantité | Notes |
|-----------|----------|-------|
| BTT Pi v1.2 | 1 | Contrôleur principal |
| A4988 | 2 | Drivers stepper |
| NEMA17 | 2 | Moteurs pas à pas |
| Webcam USB | 1 | Capture d'images |
| Alimentation 12V-24V | 1 | Pour les moteurs |

### Impression 3D
- Pièces pour le plateau tournant
- Pièces pour le bras caméra
- Support pour la webcam

## Installation

### 1. Préparer le BTT Pi

```bash
# Flasher le BTT Pi avec Raspbian ou utiliser Klipper image
# Le BTT Pi v1.2 fonctionne avec Allwinner H616

# Installer les dépendances
sudo apt update
sudo apt install -y python3-pip python3-opencv
pip3 install -r requirements.txt
```

### 2. Configurer les broches GPIO

Modifier `config.py` selon votre câblage:

```python
TURN_TABLE = {
    "step": 17,
    "dir": 27,
    "enable": 22,
    "steps_per_rev": 200,
    "microstep": 16,
}
```

### 3. Câbler les composants

Suivre le schéma de câblage dans `wiring.md`.

### 4. Lancer le scanner

```bash
# Mode terminal (test)
python3 scanner.py

# Mode interface web
python3 web_app.py
```

## Utilisation

### Interface Web

1. Ouvrir un navigateur sur `http://<IP_DU_BTT_PI>:5000`
2. Configurer les paramètres du scan
3. Cliquer sur "Démarrer le scan"

### Mode Terminal

```python
from scanner import Scanner3D

scanner = Scanner3D()

# Scan rapide
scanner.quick_scan(photos=36, arm_steps=3)

# Ou scan personnalisé
scanner.start_scan(photos_per_rotation=36, arm_positions=5)
scanner.execute_scan()
```

## Structure du projet

```
3d_scanner/
├── config.py          # Configuration des broches et paramètres
├── stepper.py         # Contrôle des moteurs pas à pas
├── camera.py          # Capture webcam
├── scanner.py         # Scanner principal (coordination)
├── web_app.py         # Interface web Flask
├── requirements.txt   # Dépendances Python
├── wiring.md          # Schéma de câblage
└── captures/          # Dossier de sortie des images
```

## Personnalisation

### Changer le nombre de photos

Dans `config.py`:
```python
SCAN_SETTINGS = {
    "photos_per_rotation": 72,  # Plus de photos = meilleure qualité
    "arm_positions": 10,        # Plus de positions = meilleure couverture
}
```

### Utiliser une autre webcam

```python
WEBCAM = {
    "device_id": 1,  # Deuxième webcam
    "resolution": (1280, 720),  # Résolution plus faible pour vitesse
}
```

## Dépannage

### La webcam ne fonctionne pas
- Vérifier que la webcam est branchée
- Tester avec: `python3 -c "import cv2; print(cv2.VideoCapture(0).isOpened())"`

### Les moteurs ne bougent pas
- Vérifier le câblage des drivers A4988
- Vérifier l'alimentation 12V-24V
- Vérifier les microstepping (MS1, MS2, MS3)

### Le serveur web ne démarre pas
- Vérifier que Flask est installé: `pip3 install flask`
- Vérifier le port 5000 n'est pas utilisé

## Licence

Projet open source - Utilisez librement pour vos projets personnels.

## Crédits

- Inspiré par [OpenScan](https://openscan.eu/) - Scanner 3D open source
- Utilise [BTT Pi v1.2](https://github.com/bigtreetech/BTT-Pi) - BigTreeTech
- Contrôle moteurs via [RPi.GPIO](https://pypi.org/project/RPi.GPIO/)
- Interface web avec [Flask](https://flask.palletsprojects.com/)
- Capture vidéo avec [OpenCV](https://opencv.org/)
