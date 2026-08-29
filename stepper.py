"""
Contrôle des moteurs pas à pas via GPIO sur BTT Pi v1.2
Utilise les drivers A4988 pour le pilotage des NEMA17
"""

import time
import RPi.GPIO as GPIO
from config import TURN_TABLE, CAMERA_ARM, SCAN_SETTINGS


class StepperMotor:
    """Classe pour contrôler un moteur pas à pas via A4988"""

    def __init__(self, config: dict, name: str = "Stepper"):
        self.name = name
        self.step_pin = config["step"]
        self.dir_pin = config["dir"]
        self.enable_pin = config.get("enable", None)
        self.steps_per_rev = config["steps_per_rev"]
        self.microstep = config["microstep"]
        self.steps_per_full_rev = self.steps_per_rev * self.microstep
        self.current_position = 0  # Position en pas

        # Configuration GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.step_pin, GPIO.OUT)
        GPIO.setup(self.dir_pin, GPIO.OUT)
        if self.enable_pin:
            GPIO.setup(self.enable_pin, GPIO.OUT)
            GPIO.output(self.enable_pin, GPIO.HIGH)  # Désactivé par défaut

        print(f"[{self.name}] Initialisé - Steps/rev: {self.steps_per_full_rev}")

    def enable(self):
        """Active le moteur"""
        if self.enable_pin:
            GPIO.output(self.enable_pin, GPIO.LOW)
            print(f"[{self.name}] Activé")

    def disable(self):
        """Désactive le moteur (libère le couple)"""
        if self.enable_pin:
            GPIO.output(self.enable_pin, GPIO.HIGH)
            print(f"[{self.name}] Désactivé")

    def move_steps(self, steps: int, delay: float = None):
        """
        Déplace le moteur d'un nombre de pas
        steps > 0: sens horaire
        steps < 0: sens anti-horaire
        """
        if delay is None:
            delay = SCAN_SETTINGS["step_delay"]

        # Définir la direction
        if steps > 0:
            GPIO.output(self.dir_pin, GPIO.HIGH)
        else:
            GPIO.output(self.dir_pin, GPIO.LOW)

        steps = abs(steps)

        # Activer le moteur
        self.enable()
        time.sleep(0.01)

        # Envoyer les pulses
        for _ in range(steps):
            GPIO.output(self.step_pin, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(self.step_pin, GPIO.LOW)
            time.sleep(delay)

        # Mettre à jour la position
        self.current_position += steps if steps > 0 else -steps

    def move_to_angle(self, angle: float, delay: float = None):
        """
        Déplace le moteur à un angle spécifique (en degrés)
        angle: -360 à 360 (ou plus pour plusieurs rotations)
        """
        steps = int((angle / 360.0) * self.steps_per_full_rev)
        self.move_steps(steps, delay)

    def move_to_percent(self, percent: float, delay: float = None):
        """
        Déplace le moteur à un pourcentage de la rotation complète
        percent: 0.0 à 100.0
        """
        angle = (percent / 100.0) * 360.0
        self.move_to_angle(angle, delay)

    def rotate_absolute(self, angle: float, delay: float = None):
        """
        Tourne vers un angle absolu (0-360°)
        Gère le chemin le plus court
        """
        current_angle = (self.current_position / self.steps_per_full_rev) * 360.0
        diff = angle - current_angle

        # Prendre le chemin le plus court
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360

        self.move_to_angle(diff, delay)

    def home(self, speed: float = 0.5):
        """Retour à la position zéro (0°)"""
        self.rotate_absolute(0, speed)
        self.current_position = 0
        print(f"[{self.name}] Retour à zéro")

    def cleanup(self):
        """Nettoie les GPIO"""
        self.disable()


class ScannerMotors:
    """Classe pour gérer les deux moteurs du scanner"""

    def __init__(self):
        print("=== Initialisation des moteurs du scanner ===")
        self.turntable = StepperMotor(TURN_TABLE, "Plateau")
        self.camera_arm = StepperMotor(CAMERA_ARM, "Bras Caméra")
        print("=== Moteurs initialisés avec succès ===\n")

    def enable_all(self):
        """Active les deux moteurs"""
        self.turntable.enable()
        self.camera_arm.enable()

    def disable_all(self):
        """Désactive les deux moteurs"""
        self.turntable.disable()
        self.camera_arm.disable()

    def scan_sequence(self, photos_per_rotation=None, arm_positions=None,
                      settle_time=None, callback=None):
        """
        Exécute une séquence de scan complète

        Args:
            photos_per_rotation: Nombre de photos par rotation
            arm_positions: Nombre de positions verticales
            settle_time: Temps d'attente entre les mouvements
            callback: Fonction appelée à chaque position (angle_plateau, angle_bras)
        """
        if photos_per_rotation is None:
            photos_per_rotation = SCAN_SETTINGS["photos_per_rotation"]
        if arm_positions is None:
            arm_positions = SCAN_SETTINGS["arm_positions"]
        if settle_time is None:
            settle_time = SCAN_SETTINGS["settle_time"]

        angle_step = 360.0 / photos_per_rotation
        arm_step = 90.0 / (arm_positions - 1) if arm_positions > 1 else 90

        print(f"\n=== Début du scan ===")
        print(f"Photos par rotation: {photos_per_rotation}")
        print(f"Positions verticales: {arm_positions}")
        print(f"Total photos estimé: {photos_per_rotation * arm_positions}")

        total_photos = 0

        for arm_idx in range(arm_positions):
            arm_angle = arm_idx * arm_step
            print(f"\n--- Position bras: {arm_angle:.1f}° ({arm_idx + 1}/{arm_positions}) ---")

            # Déplacer le bras
            self.camera_arm.rotate_absolute(arm_angle)
            time.sleep(settle_time)

            for photo_idx in range(photos_per_rotation):
                table_angle = photo_idx * angle_step

                # Tourner le plateau
                self.turntable.rotate_absolute(table_angle)
                time.sleep(settle_time)

                total_photos += 1
                print(f"  Photo {total_photos}: Plateau={table_angle:.1f}°, Bras={arm_angle:.1f}°")

                # Appeler le callback si fourni
                if callback:
                    callback(table_angle, arm_angle, total_photos)

        print(f"\n=== Scan terminé - {total_photos} photos ===")
        return total_photos

    def cleanup(self):
        """Nettoie les GPIO"""
        self.turntable.cleanup()
        self.camera_arm.cleanup()
        GPIO.cleanup()
        print("GPIO nettoyés")


if __name__ == "__main__":
    # Test des moteurs
    try:
        motors = ScannerMotors()

        print("\nTest: Tourner le plateau de 90°")
        motors.turntable.rotate_absolute(90)
        time.sleep(1)

        print("Test: Tourner le bras de 45°")
        motors.camera_arm.rotate_absolute(45)
        time.sleep(1)

        print("Test: Retour à zéro")
        motors.turntable.home()
        motors.camera_arm.home()

    except KeyboardInterrupt:
        print("\nArrêt par l'utilisateur")
    finally:
        motors.cleanup()
