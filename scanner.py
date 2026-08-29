"""
Scanner 3D principal
Coordonne les moteurs et la caméra pour effectuer un scan complet
"""

import os
import time
import json
from datetime import datetime
from stepper import ScannerMotors
from camera import WebcamCapture
from config import SCAN_SETTINGS


class Scanner3D:
    """Classe principale du scanner 3D"""

    def __init__(self, output_dir="captures"):
        """
        Initialise le scanner

        Args:
            output_dir: Dossier de sortie pour les images
        """
        print("=== Initialisation du Scanner 3D ===\n")

        # Initialiser les moteurs
        self.motors = ScannerMotors()

        # Initialiser la caméra
        self.camera = WebcamCapture(output_dir=output_dir)

        # État du scan
        self.current_scan = None
        self.is_scanning = False

        # Charger la configuration du dernier scan si disponible
        self.config_file = os.path.join(output_dir, "scan_config.json")

        print("\n=== Scanner initialisé avec succès ===\n")

    def start_scan(self, photos_per_rotation=None, arm_positions=None,
                   project_name=None, settle_time=None):
        """
        Démarre un nouveau scan

        Args:
            photos_per_rotation: Nombre de photos par rotation du plateau
            arm_positions: Nombre de positions verticales du bras
            project_name: Nom du projet (défaut: timestamp)
            settle_time: Temps d'attente après mouvement

        Returns:
            scan_id: Identifiant du scan
        """
        if self.is_scanning:
            print("[Scanner] Un scan est déjà en cours!")
            return None

        # Paramètres par défaut
        if photos_per_rotation is None:
            photos_per_rotation = SCAN_SETTINGS["photos_per_rotation"]
        if arm_positions is None:
            arm_positions = SCAN_SETTINGS["arm_positions"]
        if settle_time is None:
            settle_time = SCAN_SETTINGS["settle_time"]
        if project_name is None:
            project_name = datetime.now().strftime("scan_%Y%m%d_%H%M%S")

        # Créer la structure de dossiers
        scan_dir = os.path.join(self.camera.output_dir, project_name)
        os.makedirs(scan_dir, exist_ok=True)

        # Initialiser le scan
        self.current_scan = {
            "id": project_name,
            "start_time": datetime.now().isoformat(),
            "photos_per_rotation": photos_per_rotation,
            "arm_positions": arm_positions,
            "settle_time": settle_time,
            "status": "en cours",
            "photos_captured": 0,
            "total_estimated": photos_per_rotation * arm_positions,
        }

        # Sauvegarder la config
        self._save_scan_config()

        print(f"[Scanner] Scan démarré: {project_name}")
        print(f"  Photos par rotation: {photos_per_rotation}")
        print(f"  Positions verticales: {arm_positions}")
        print(f"  Total estimé: {self.current_scan['total_estimated']}")

        self.is_scanning = True
        return project_name

    def execute_scan(self, callback=None):
        """
        Exécute le scan (doit être appelé après start_scan)

        Args:
            callback: Fonction appelée pour chaque photo
                     callback(chemin_image, angle_plateau, angle_bras, numero)

        Returns:
            results: Dictionnaire avec les résultats du scan
        """
        if not self.is_scanning or not self.current_scan:
            print("[Scanner] Aucun scan en cours. Utilisez start_scan() d'abord.")
            return None

        scan_id = self.current_scan["id"]
        photos_per_rotation = self.current_scan["photos_per_rotation"]
        arm_positions = self.current_scan["arm_positions"]
        settle_time = self.current_scan["settle_time"]

        angle_step = 360.0 / photos_per_rotation
        arm_step = 90.0 / (arm_positions - 1) if arm_positions > 1 else 90

        print(f"\n{'='*50}")
        print(f"EXÉCUTION DU SCAN: {scan_id}")
        print(f"{'='*50}\n")

        results = {
            "scan_id": scan_id,
            "photos": [],
            "start_time": datetime.now().isoformat(),
        }

        photo_count = 0

        try:
            # Ouvrir la caméra
            if not self.camera.open():
                raise Exception("Impossible d'ouvrir la webcam")

            for arm_idx in range(arm_positions):
                arm_angle = arm_idx * arm_step
                print(f"\n--- Position bras: {arm_angle:.1f}° ({arm_idx + 1}/{arm_positions}) ---")

                # Déplacer le bras
                self.motors.camera_arm.rotate_absolute(arm_angle)
                time.sleep(settle_time)

                # Créer le sous-dossier pour cette position du bras
                arm_dir = f"arm_{arm_idx:02d}"
                arm_path = os.path.join(self.camera.output_dir, scan_id, arm_dir)
                os.makedirs(arm_path, exist_ok=True)

                for photo_idx in range(photos_per_rotation):
                    table_angle = photo_idx * angle_step

                    # Tourner le plateau
                    self.motors.turntable.rotate_absolute(table_angle)
                    time.sleep(settle_time)

                    # Capturer l'image
                    filename = f"photo_{arm_idx:02d}_{photo_idx:03d}.jpg"
                    filepath = self.camera.save_image(
                        self.camera.capture_frame(),
                        filename=filename,
                        subdir=os.path.join(scan_id, arm_dir)
                    )

                    photo_count += 1
                    self.current_scan["photos_captured"] = photo_count

                    # Enregistrer la photo
                    photo_info = {
                        "file": filepath,
                        "table_angle": table_angle,
                        "arm_angle": arm_angle,
                        "index": photo_count,
                    }
                    results["photos"].append(photo_info)

                    print(f"  [{photo_count}/{self.current_scan['total_estimated']}] "
                          f"Plateau={table_angle:.1f}° Bras={arm_angle:.1f}° -> {filename}")

                    # Callback
                    if callback:
                        callback(filepath, table_angle, arm_angle, photo_count)

                    # Sauvegarder la config périodiquement
                    if photo_count % 10 == 0:
                        self._save_scan_config()

        except Exception as e:
            print(f"\n[Scanner] ERREUR: {e}")
            self.current_scan["status"] = "erreur"
            self.current_scan["error"] = str(e)
        else:
            self.current_scan["status"] = "terminé"
            print(f"\n{'='*50}")
            print(f"SCAN TERMINÉ: {photo_count} photos capturées")
            print(f"{'='*50}")

        finally:
            self.current_scan["end_time"] = datetime.now().isoformat()
            self._save_scan_config()
            self.is_scanning = False

            # Retour à la position initiale
            print("\nRetour à la position initiale...")
            self.motors.turntable.home()
            self.motors.camera_arm.home()

        results["total_photos"] = photo_count
        results["end_time"] = datetime.now().isoformat()
        return results

    def quick_scan(self, photos=36, arm_steps=3):
        """
        Scan rapide avec paramètres prédéfinis

        Args:
            photos: Nombre total de photos souhaitées
            arm_steps: Nombre de positions verticales

        Returns:
            results: Résultats du scan
        """
        photos_per_rotation = photos // arm_steps
        project_name = f"quick_{datetime.now().strftime('%H%M%S')}"

        self.start_scan(
            photos_per_rotation=photos_per_rotation,
            arm_positions=arm_steps,
            project_name=project_name
        )
        return self.execute_scan()

    def calibrate(self):
        """
        Procédure de calibration des moteurs
        Déplace les moteurs dans les positions limites
        """
        print("\n=== Calibration des moteurs ===")

        print("1. Calibration du plateau (0°, 90°, 180°, 270°, 360°)")
        for angle in [0, 90, 180, 270, 360]:
            self.motors.turntable.rotate_absolute(angle)
            time.sleep(1)
            print(f"   Plateau à {angle}°")

        print("\n2. Calibration du bras (0°, 45°, 90°)")
        for angle in [0, 45, 90]:
            self.motors.camera_arm.rotate_absolute(angle)
            time.sleep(1)
            print(f"   Bras à {angle}°")

        # Retour à la position initiale
        print("\n3. Retour à la position initiale")
        self.motors.turntable.home()
        self.motors.camera_arm.home()

        print("\n=== Calibration terminée ===")

    def _save_scan_config(self):
        """Sauvegarde la configuration du scan en cours"""
        if self.current_scan:
            try:
                with open(self.config_file, 'w') as f:
                    json.dump(self.current_scan, f, indent=2)
            except Exception as e:
                print(f"[Scanner] Erreur sauvegarde config: {e}")

    def get_status(self):
        """Retourne le statut actuel du scanner"""
        return {
            "is_scanning": self.is_scanning,
            "current_scan": self.current_scan,
            "motors": {
                "turntable_position": self.motors.turntable.current_position,
                "arm_position": self.motors.camera_arm.current_position,
            },
            "camera": self.camera.get_camera_info(),
        }

    def cleanup(self):
        """Nettoie les ressources"""
        print("\n=== Arrêt du scanner ===")
        self.motors.cleanup()
        self.camera.close()
        print("=== Scanner arrêté ===")


if __name__ == "__main__":
    # Test du scanner
    scanner = None
    try:
        scanner = Scanner3D()

        print("\nOptions:")
        print("1. Scan rapide (36 photos)")
        print("2. Calibration")
        print("3. Aperçu caméra")
        print("4. Quitter")

        choice = input("\nVotre choix (1-4): ").strip()

        if choice == "1":
            results = scanner.quick_scan(photos=36, arm_steps=3)
            print(f"\nRésultats: {results['total_photos']} photos")

        elif choice == "2":
            scanner.calibrate()

        elif choice == "3":
            scanner.camera.preview(duration=10)

        else:
            print("Au revoir!")

    except KeyboardInterrupt:
        print("\nArrêt par l'utilisateur")
    finally:
        if scanner:
            scanner.cleanup()
