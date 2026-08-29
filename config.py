# Configuration du scanner 3D

# === Configuration Arduino (CNC Shield V3) ===
ARDUINO = {
    "port": None,          # None = auto-détection, ou "/dev/ttyUSB0", "COM3", etc.
    "baudrate": 115200,
}

# === Paramètres des moteurs ===
# Les moteurs sont contrôlés par l'Arduino via le CNC Shield V3
# X = Plateau tournant, Y = Bras caméra
TURN_TABLE = {
    "axis": "X",
    "steps_per_rev": 200,   # 200 pas/rev pour NEMA17 (1.8°/pas)
    "microstep": 16,        # Microstepping sur les A4988 (jumper sur le shield)
}

CAMERA_ARM = {
    "axis": "Z",
    "steps_per_rev": 200,
    "microstep": 16,
}

# === Paramètres du scan ===
SCAN_SETTINGS = {
    "photos_per_rotation": 36,    # Nombre de photos par rotation complète
    "arm_positions": 5,           # Nombre de positions verticales du bras
    "settle_time": 0.5,           # Temps d'attente après mouvement (secondes)
}

# === Webcam ===
WEBCAM = {
    "device_id": 0,               # ID de la webcam (0 = première webcam détectée)
    "resolution": (1920, 1080),   # Résolution de capture
    "output_dir": "captures",     # Dossier de sortie des images
}

# === Interface web ===
WEB_INTERFACE = {
    "host": "0.0.0.0",
    "port": 5000,
}
