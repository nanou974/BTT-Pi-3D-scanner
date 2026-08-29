"""
Module de capture webcam pour le scanner 3D
Utilise OpenCV pour la capture d'images via USB webcam
"""

import cv2
import os
import time
from datetime import datetime
from config import WEBCAM


class WebcamCapture:
    """Classe pour gérer la capture d'images via webcam USB"""

    def __init__(self, device_id=None, resolution=None, output_dir=None):
        """
        Initialise la webcam

        Args:
            device_id: ID de la webcam (défaut: config)
            resolution: Tuple (largeur, hauteur) pour l'aperçu (défaut: config)
            output_dir: Dossier de sortie (défaut: config)
        """
        self.device_id = device_id or WEBCAM["device_id"]
        self.resolution = resolution or WEBCAM["resolution"]
        self.capture_resolution = WEBCAM.get("capture_resolution", self.resolution)
        self.output_dir = output_dir or WEBCAM["output_dir"]
        self.cap = None
        self.is_opened = False

        # Créer le dossier de sortie
        os.makedirs(self.output_dir, exist_ok=True)

        print(f"[Caméra] Initialisation - Device: {self.device_id}, Aperçu: {self.resolution}, Capture: {self.capture_resolution}")

    def open(self):
        """Ouvre la connexion à la webcam"""
        try:
            self.cap = cv2.VideoCapture(self.device_id)
            if not self.cap.isOpened():
                raise Exception(f"Impossible d'ouvrir la webcam {self.device_id}")

            # Configurer la résolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])

            # Vérifier la résolution réelle
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"[Caméra] Résolution actuelle: {actual_width}x{actual_height}")

            self.is_opened = True
            print("[Caméra] Webcam ouverte avec succès")
            return True

        except Exception as e:
            print(f"[Caméra] Erreur lors de l'ouverture: {e}")
            self.is_opened = False
            return False

    def capture_frame(self):
        """
        Capture une image unique

        Returns:
            image: Array numpy de l'image capturée, ou None en cas d'erreur
        """
        if not self.is_opened:
            if not self.open():
                return None

        ret, frame = self.cap.read()
        if ret:
            return frame
        else:
            print("[Caméra] Erreur de capture")
            return None

    def save_image(self, frame, filename=None, subdir=None):
        """
        Sauvegarde une image sur le disque

        Args:
            frame: Image à sauvegarder (array numpy)
            filename: Nom du fichier (défaut: timestamp)
            subdir: Sous-dossier dans output_dir

        Returns:
            filepath: Chemin complet du fichier sauvegardé
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"scan_{timestamp}.jpg"

        # Construire le chemin
        save_dir = self.output_dir
        if subdir:
            save_dir = os.path.join(self.output_dir, subdir)
            os.makedirs(save_dir, exist_ok=True)

        filepath = os.path.join(save_dir, filename)

        # Sauvegarder
        cv2.imwrite(filepath, frame)
        print(f"[Caméra] Image sauvegardée: {filepath}")
        return filepath

    def capture_and_save(self, subdir=None, prefix="scan"):
        """
        Capture et sauvegarde une image en une seule opération
        Utilise la résolution de capture pour une meilleure qualité

        Returns:
            filepath: Chemin de l'image sauvegardée
        """
        if not self.is_opened:
            if not self.open():
                return None

        # Passer en résolution de capture
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.capture_resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.capture_resolution[1])
        time.sleep(0.3)  # Laisser le temps à la webcam d'ajuster

        frame = self.capture_frame()

        # Repasser en résolution d'aperçu
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])

        if frame is not None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{prefix}_{timestamp}.jpg"
            return self.save_image(frame, filename, subdir)
        return None

    def preview(self, duration=5):
        """
        Affiche un aperçu en direct de la webcam

        Args:
            duration: Durée en secondes (0 = infini until 'q' pressed)
        """
        if not self.is_opened:
            if not self.open():
                return

        print("[Caméra] Aperçu en direct - Appuyez sur 'q' pour quitter")
        start_time = time.time()

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("[Caméra] Erreur de capture")
                break

            # Afficher l'image
            cv2.imshow("Aperçu Scanner 3D", frame)

            # Vérifier la touche 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # Vérifier la durée
            if duration > 0 and (time.time() - start_time) > duration:
                break

        cv2.destroyAllWindows()
        print("[Caméra] Aperçu terminé")

    def capture_batch(self, count, interval=1.0, subdir="batch"):
        """
        Capture un lot d'images avec un intervalle

        Args:
            count: Nombre d'images à capturer
            interval: Intervalle entre les captures (secondes)
            subdir: Sous-dossier pour les images

        Returns:
            files: Liste des fichiers capturés
        """
        files = []
        print(f"[Caméra] Début de la capture de {count} images")

        for i in range(count):
            filepath = self.capture_and_save(subdir=subdir, prefix=f"batch_{i:04d}")
            if filepath:
                files.append(filepath)
                print(f"[Caméra] Capture {i + 1}/{count}")

            if i < count - 1:
                time.sleep(interval)

        print(f"[Caméra] {len(files)} images capturées dans {subdir}/")
        return files

    def get_camera_info(self):
        """Retourne les informations de la webcam"""
        if not self.is_opened:
            return {"status": "fermée"}

        info = {
            "device_id": self.device_id,
            "resolution": (
                int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            ),
            "fps": self.cap.get(cv2.CAP_PROP_FPS),
            "backend": self.cap.getBackendName(),
        }
        return info

    def close(self):
        """Ferme la connexion à la webcam"""
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.is_opened = False
            print("[Caméra] Webcam fermée")

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


if __name__ == "__main__":
    # Test de la webcam
    try:
        cam = WebcamCapture()

        print("\nTest: Informations caméra")
        if cam.open():
            info = cam.get_camera_info()
            print(f"  {info}")

            print("\nTest: Capture d'une image")
            filepath = cam.capture_and_save(subdir="test")
            print(f"  Image sauvegardée: {filepath}")

            print("\nTest: Aperçu 5 secondes")
            cam.preview(duration=5)

            cam.close()
        else:
            print("Impossible d'ouvrir la webcam")

    except KeyboardInterrupt:
        print("\nArrêt par l'utilisateur")
    finally:
        if 'cam' in locals():
            cam.close()
