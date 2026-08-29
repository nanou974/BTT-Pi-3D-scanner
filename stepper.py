"""
Contrôle des moteurs pas à pas via Arduino Uno + CNC Shield V3
Communication série USB avec le BTT Pi v1.2
"""

import time
import serial
import serial.tools.list_ports
from config import TURN_TABLE, CAMERA_ARM, SCAN_SETTINGS


class ArduinoController:
    """Contrôleur série pour Arduino Uno"""

    def __init__(self, port=None, baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.connected = False

        if self.port is None:
            self.port = self._find_arduino()

    def _find_arduino(self):
        """Détecte automatiquement le port Arduino"""
        ports = serial.tools.list_ports.comports()
        for p in ports:
            desc = p.description.lower()
            if 'arduino' in desc or 'ch340' in desc or 'cp210' in desc or 'ftdi' in desc:
                print(f"[Arduino] Port détecté: {p.device} ({p.description})")
                return p.device
        # Fallback: chercher tout port USB série
        for p in ports:
            if 'usb' in p.device.lower() or 'ttyacm' in p.device.lower() or 'ttyusb' in p.device.lower():
                print(f"[Arduino] Port USB détecté: {p.device} ({p.description})")
                return p.device
        return None

    def connect(self):
        """Connecte à l'Arduino"""
        if self.port is None:
            print("[Arduino] Aucun port détecté!")
            return False

        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=2)
            time.sleep(2)  # Attendre le reset de l'Arduino

            # Attendre le message de prêt
            response = self._read_response(timeout=5)
            if response and "SCANNER3D_RDY" in response:
                print(f"[Arduino] Connecté sur {self.port}")
                self.connected = True
                return True
            else:
                print(f"[Arduino] Pas de réponse Arduino (reçu: {response})")
                self.ser.close()
                self.connected = False
                return False

        except Exception as e:
            print(f"[Arduino] Erreur connexion: {e}")
            self.connected = False
            return False

    def send_command(self, cmd, timeout=30):
        """Envoie une commande et attend la réponse"""
        if not self.ser or not self.connected:
            return None

        try:
            self.ser.reset_input_buffer()
            self.ser.write((cmd + "\n").encode())
            return self._read_response(timeout=timeout)
        except Exception as e:
            print(f"[Arduino] Erreur envoi: {e}")
            return None

    def _read_response(self, timeout=30):
        """Lit la réponse de l'Arduino"""
        response = ""
        start = time.time()
        while time.time() - start < timeout:
            if self.ser.in_waiting:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    response += line + " "
                    if "OK" in line or "ERR" in line:
                        return response.strip()
            time.sleep(0.01)
        return response.strip() if response else None

    def is_ready(self):
        """Vérifie si l'Arduino est connecté"""
        resp = self.send_command("OK")
        return resp and "OK" in resp

    def disconnect(self):
        """Déconnecte l'Arduino"""
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.connected = False
        print("[Arduino] Déconnecté")


class StepperMotor:
    """Classe pour contrôler un moteur via Arduino"""

    def __init__(self, config: dict, name: str = "Stepper", axis: str = "X"):
        self.name = name
        self.axis = axis
        self.steps_per_rev = config["steps_per_rev"]
        self.microstep = config["microstep"]
        self.steps_per_full_rev = self.steps_per_rev * self.microstep
        self.current_position = 0
        self.arduino = None

        print(f"[{self.name}] Initialisé - Steps/rev: {self.steps_per_full_rev}, Axe: {axis}")

    def set_controller(self, arduino: ArduinoController):
        """Définit le contrôleur Arduino"""
        self.arduino = arduino

    def enable(self):
        """Active les moteurs"""
        if self.arduino:
            self.arduino.send_command("ENABLE")
            print(f"[{self.name}] Activé")

    def disable(self):
        """Désactive les moteurs"""
        if self.arduino:
            self.arduino.send_command("DISABLE")
            print(f"[{self.name}] Désactivé")

    def move_steps(self, steps: int, delay: float = None):
        """Déplace le moteur d'un nombre de pas"""
        if not self.arduino or not self.arduino.connected:
            print(f"[{self.name}] Arduino non connecté!")
            return

        cmd = f"M{self.axis}{int(steps)}"
        self.arduino.send_command(cmd, timeout=60)

        self.current_position += steps

    def move_to_angle(self, angle: float, delay: float = None):
        """Déplace le moteur à un angle spécifique (en degrés)"""
        steps = int((angle / 360.0) * self.steps_per_full_rev)
        self.move_steps(steps, delay)

    def move_to_percent(self, percent: float, delay: float = None):
        """Déplace le moteur à un pourcentage de la rotation complète"""
        angle = (percent / 100.0) * 360.0
        self.move_to_angle(angle, delay)

    def rotate_absolute(self, angle: float, delay: float = None):
        """Tourne vers un angle absolu (0-360°)"""
        current_angle = (self.current_position / self.steps_per_full_rev) * 360.0
        diff = angle - current_angle

        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360

        self.move_to_angle(diff, delay)

    def home(self, speed: float = 0.5):
        """Retour à la position zéro"""
        if self.arduino:
            self.arduino.send_command("HOME")
        self.current_position = 0
        print(f"[{self.name}] Retour à zéro")

    def cleanup(self):
        """Nettoie"""
        self.disable()


class ScannerMotors:
    """Classe pour gérer les deux moteurs du scanner"""

    def __init__(self, port=None):
        print("=== Initialisation des moteurs du scanner ===")

        self.arduino = ArduinoController(port=port)
        if not self.arduino.connect():
            print("ATTENTION: Arduino non connectée. Les moteurs ne fonctionneront pas.")

        self.turntable = StepperMotor(TURN_TABLE, "Plateau", axis="X")
        self.camera_arm = StepperMotor(CAMERA_ARM, "Bras Caméra", axis="Y")

        self.turntable.set_controller(self.arduino)
        self.camera_arm.set_controller(self.arduino)

        print("=== Moteurs initialisés avec succès ===\n")

    def enable_all(self):
        """Active les deux moteurs"""
        self.arduino.send_command("ENABLE")

    def disable_all(self):
        """Désactive les deux moteurs"""
        self.arduino.send_command("DISABLE")

    def scan_sequence(self, photos_per_rotation=None, arm_positions=None,
                      settle_time=None, callback=None):
        """Exécute une séquence de scan complète"""
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

            self.camera_arm.rotate_absolute(arm_angle)
            time.sleep(settle_time)

            for photo_idx in range(photos_per_rotation):
                table_angle = photo_idx * angle_step

                self.turntable.rotate_absolute(table_angle)
                time.sleep(settle_time)

                total_photos += 1
                print(f"  Photo {total_photos}: Plateau={table_angle:.1f}°, Bras={arm_angle:.1f}°")

                if callback:
                    callback(table_angle, arm_angle, total_photos)

        print(f"\n=== Scan terminé - {total_photos} photos ===")
        return total_photos

    def cleanup(self):
        """Nettoie les ressources"""
        self.turntable.cleanup()
        self.camera_arm.cleanup()
        self.arduino.disconnect()
        print("Moteurs nettoyés")


if __name__ == "__main__":
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
