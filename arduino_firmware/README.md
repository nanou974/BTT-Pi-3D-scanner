# Firmware Arduino pour Scanner 3D

## Matériel
- Arduino Uno (ou clone CH340)
- CNC Shield V3
- 2x A4988 drivers (déjà montés sur le shield)
- 2x NEMA17 moteurs pas à pas

## Installation

### 1. Flasher le firmware

**Option A : Arduino IDE (recommandé)**
1. Ouvrir Arduino IDE
2. Ouvrir `scanner3d.ino`
3. Sélectionner "Arduino Uno" comme carte
4. Sélectionner le bon port série
5. Cliquer "Upload"

**Option B : arduino-cli**
```bash
arduino-cli compile --fqbn arduino:avr:uno scanner3d.ino
arduino-cli upload -p /dev/ttyUSB0 --fqbn arduino:avr:uno scanner3d.ino
```

### 2. Configurer les microstepping

Sur le CNC Shield V3, les jumpers MS1/MS2/MS3 définissent le microstepping.

Pour 1/16 microstep (recommandé pour ce projet):
- MS1, MS2, MS3 = HIGH (jumper présents)

### 3. Connecter l'alimentation

- Brancher une alimentation 12V-24V sur le bornier bleu du shield
- L'Arduino est alimenté par USB en même temps

## Protocol série

Baudrate: 115200

| Commande | Description | Réponse |
|----------|-------------|---------|
| `OK` | Test de connexion | `OK` |
| `MX<steps>` | Déplacer axe X (plateau) | `OK` |
| `MY<steps>` | Déplacer axe Y (bras) | `OK` |
| `MZ<steps>` | Déplacer axe Z (libre) | `OK` |
| `HOME` | Retour au zéro logiciel | `OK` |
| `STATUS` | Positions actuelles | `POS X:0 Y:0` |
| `ENABLE` | Activer les moteurs | `OK` |
| `DISABLE` | Désactiver les moteurs | `OK` |
| `RESET` | Reset positions à zéro | `OK` |
| `SPEED<val>` | Vitesse (µs/pas, défaut:500) | `OK SPEED:500` |

## Test rapide

Avec le moniteur série Arduino IDE (115200 baud):
```
OK          → SCANNER3D_RDY ou OK
ENABLE      → OK
MX1600      → OK (1 tour à 1/16 microstep)
MY800       → OK (demi-tour)
HOME        → OK
DISABLE     → OK
```

## Pinout CNC Shield V3

| Fonction | Pin Arduino |
|----------|-------------|
| X.STEP | 2 |
| X.DIR | 5 |
| Y.STEP | 3 |
| Y.DIR | 6 |
| Z.STEP | 4 |
| Z.DIR | 7 |
| EN | 8 |
