#!/usr/bin/env python3
"""
Bouton physique pour basculer entre Hotspot et Client WiFi
Branche un tact switch entre le GPIO et GND
"""

import subprocess
import time
import sys
import os

# GPIO du bouton (BCM) - à adapter selon ton câblage
BUTTON_GPIO = 17

def get_network_mode():
    """Vérifie le mode réseau actuel"""
    try:
        result = subprocess.run(['systemctl', 'is-active', 'hostapd'],
                                capture_output=True, text=True)
        return 'hotspot' if result.stdout.strip() == 'active' else 'client'
    except:
        return 'client'

def switch_mode():
    """Bascule entre hotspot et client"""
    current = get_network_mode()
    script_dir = os.path.dirname(os.path.abspath(__file__))

    if current == 'hotspot':
        print("[Button] Bascule en mode client...")
        subprocess.Popen(['bash', os.path.join(script_dir, 'hotspot_off.sh')])
    else:
        print("[Button] Bascule en mode hotspot...")
        subprocess.Popen(['bash', os.path.join(script_dir, 'hotspot_on.sh')])

def main():
    # Initialiser RPi.GPIO
    try:
        import RPi.GPIO as GPIO
    except ImportError:
        print("[Button] RPi.GPIO non disponible. Installation...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'RPi.GPIO'])
        import RPi.GPIO as GPIO

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    print(f"[Button] Botão configuré sur GPIO {BUTTON_GPIO}")
    print(f"[Button] Mode actuel: {get_network_mode()}")

    last_state = GPIO.input(BUTTON_GPIO)
    last_press = 0

    try:
        while True:
            state = GPIO.input(BUTTON_GPIO)

            # Détection front descendant (appui)
            if state == GPIO.LOW and last_state == GPIO.HIGH:
                now = time.time()
                if now - last_press > 2:  # Debounce 2 secondes
                    last_press = now
                    switch_mode()

            last_state = state
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n[Button] Arrêt")
    finally:
        GPIO.cleanup()

if __name__ == '__main__':
    main()
