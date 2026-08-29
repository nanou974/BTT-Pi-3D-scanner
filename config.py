# Configuration du scanner 3D

# === Broches GPIO pour les drivers A4988 ===
# Driver du plateau tournant (NEMA17 #1)
TURN_TABLE = {
    "step": 17,      # Broche GPIO pour STEP
    "dir": 27,       # Broche GPIO pour DIR
    "enable": 22,    # Broche GPIO pour ENABLE (optionnel)
    "steps_per_rev": 200,  # 200 pas/rev pour NEMA17 (1.8°/pas)
    "microstep": 16,      # Microstepping: 1, 2, 4, 8, 16
}

# Driver du bras caméra (NEMA17 #2)
CAMERA_ARM = {
    "step": 23,
    "dir": 24,
    "enable": 25,
    "steps_per_rev": 200,
    "microstep": 16,
}

# === Paramètres du scan ===
SCAN_SETTINGS = {
    "photos_per_rotation": 36,    # Nombre de photos par rotation complète
    "arm_positions": 5,           # Nombre de positions verticales du bras
    "step_delay": 0.001,          # Délai entre les pas (secondes)
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
