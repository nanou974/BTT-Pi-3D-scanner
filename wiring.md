# Schéma de câblage - Scanner 3D

## Composants

| Composant | Quantité | Description |
|-----------|----------|-------------|
| BTT Pi v1.2 | 1 | Carte principale (Allwinner H616, 1GB RAM) |
| A4988 | 2 | Drivers pour moteurs pas à pas |
| NEMA17 | 2 | Moteurs pas à pas (1 pour plateau, 1 pour bras) |
| Webcam USB | 1 | Capture d'images |
| Alimentation 12V-24V | 1 | Pour les moteurs |
| Alimentation 5V USB-C | 1 | Pour le BTT Pi |

## Câblage des drivers A4988 au BTT Pi v1.2

### Driver 1 - Plateau tournant (NEMA17 #1)

| Broche A4988 | Broche BTT Pi | GPIO BCM |
|--------------|---------------|----------|
| STEP | Pin 11 | GPIO 17 |
| DIR | Pin 13 | GPIO 27 |
| ENABLE | Pin 15 | GPIO 22 |
| MS1 | 3.3V | - |
| MS2 | 3.3V | - |
| MS3 | 3.3V | - |
| VMOT | 12V-24V | - |
| GND (motors) | GND alimentation | - |
| GND (logic) | GND BTT Pi | - |
| 1A, 1B | NEMA17 bobine 1 | - |
| 2A, 2B | NEMA17 bobine 2 | - |

### Driver 2 - Bras caméra (NEMA17 #2)

| Broche A4988 | Broche BTT Pi | GPIO BCM |
|--------------|---------------|----------|
| STEP | Pin 16 | GPIO 23 |
| DIR | Pin 18 | GPIO 24 |
| ENABLE | Pin 22 | GPIO 25 |
| MS1 | 3.3V | - |
| MS2 | 3.3V | - |
| MS3 | 3.3V | - |
| VMOT | 12V-24V | - |
| GND (motors) | GND alimentation | - |
| GND (logic) | GND BTT Pi | - |
| 1A, 1B | NEMA17 bobine 1 | - |
| 2A, 2B | NEMA17 bobine 2 | - |

## Configuration des microstepping (A4988)

Pour un pilotage précis, utiliser 16 microsteps:

| MS1 | MS2 | MS3 | Microstep |
|-----|-----|-----|-----------|
| HIGH | HIGH | HIGH | 1/16 |

## Schéma de câblage GPIO (BTT Pi v1.2)

```
BTT Pi v1.2 - Vue du dessus
┌─────────────────────────────────────┐
│                                     │
│  ┌─────────────────────────────┐    │
│  │         40-pin GPIO         │    │
│  │  (Broches numérotées de     │    │
│  │   haut en bas, gauche       │    │
│  │   puis droite)              │    │
│  └─────────────────────────────┘    │
│                                     │
│  [USB] [USB] [USB] [USB]            │
│                                     │
│  [HDMI]        [USB-C Power]        │
│                                     │
└─────────────────────────────────────┘

Broches utilisées:
- Pin 11 (GPIO 17) -> STEP Driver 1 (Plateau)
- Pin 13 (GPIO 27) -> DIR Driver 1 (Plateau)
- Pin 15 (GPIO 22) -> ENABLE Driver 1 (Plateau)
- Pin 16 (GPIO 23) -> STEP Driver 2 (Bras)
- Pin 18 (GPIO 24) -> DIR Driver 2 (Bras)
- Pin 22 (GPIO 25) -> ENABLE Driver 2 (Bras)
- Pin 1  (3.3V)    -> MS1, MS2, MS3 (les deux drivers)
- Pin 6  (GND)     -> GND (les deux drivers)
```

## Configuration des microstepping

Par défaut, le code utilise 16 microsteps (MS1, MS2, MS3 = HIGH).

Pour changer, modifier dans `config.py`:
```python
TURN_TABLE = {
    "microstep": 16,  # 1, 2, 4, 8, ou 16
    ...
}
```

## Alimentation

### Option 1: Alimentation unique 12V-24V
- Branchez l'alimentation 12V-24V sur les borniers du BTT Pi
- Le BTT Pi génère le 5V pour lui-même via son régulateur
- Les moteurs sont alimentés directement par le 12V-24V

### Option 2: Deux alimentations séparées
- BTT Pi: Alimentation USB-C 5V/3A
- Moteurs: Alimentation externe 12V-24V sur les drivers A4988

## Webcam

Brancher la webcam USB sur l'un des 4 ports USB du BTT Pi.

## Bouton physique Hotspot/Client

Tact switch 12mm entre GPIO 17 et GND (pull-up interne activé).

```
Tact switch 12mm
   ┌───┐
   │   │
   └─┬─┘
     │
     ├──── GPIO 17 (Pin 11)
     │
    [R] 10kΩ (optionnel, pull-up interne déjà activé)
     │
    3.3V (Pin 1)

   L'autre broche → GND (Pin 6)
```

**Installation du service :**
```bash
sudo cp network-button.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable network-button
sudo systemctl start network-button
```

**Fonctionnement :**
- Appui court (< 2s) → Bascule entre hotspot et client
- LED verte = mode client, LED rouge = mode hotspot (à adapter selon ton hardware)

## Branchement des moteurs NEMA17

Les NEMA17 ont 4 fils (2 bobines). Pour identifier les bobines:
1. Les fils de même couleur (généralement) sont de la même bobine
2. Utiliser un multimètre en mode résistance: les fils de la même bobine ont une résistance faible entre eux

Connexion typique:
- Fils 1A/1B -> Bobine 1 du moteur
- Fils 2A/2B -> Bobine 2 du moteur

## Sécurité

⚠️ **Attention:**
- Débranchez l'alimentation avant de modifier le câblage
- Vérifiez le sens des moteurs avant de les connecter (peut être inversé)
- Les drivers A4988 chauffent, prévoir un dissipateur
- Ne pas dépasser 2A par phase pour les NEMA17 avec A4988
