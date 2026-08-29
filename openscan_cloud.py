"""
Module d'intégration OpenScan Cloud
Upload des photos et lancement du traitement photogrammétrie
"""

import os
import io
import zipfile
import requests
import time
from config import OPENSCAN_CLOUD


# === API Endpoints ===
API_BASE = "https://openscan.de/api/v1"
AUTH = (OPENSCAN_CLOUD["username"], OPENSCAN_CLOUD["password"])


class OpenScanCloud:
    """Client pour l'API OpenScan Cloud"""

    def __init__(self, token=None):
        self.token = token or OPENSCAN_CLOUD.get("token", "")
        self.session = requests.Session()
        self.session.auth = AUTH

    def request_token(self, email, forename, lastname):
        """
        Demande un token OpenScan Cloud

        Args:
            email: Adresse email
            forename: Prénom
            lastname: Nom

        Returns:
            dict: Réponse de l'API
        """
        resp = self.session.get(f"{API_BASE}/requestToken", params={
            "mail": email,
            "forename": forename,
            "lastname": lastname,
        })
        return resp.json()

    def get_token_info(self):
        """
        Récupère les informations du token (crédit, limites)

        Returns:
            dict: credit, limit_filesize, limit_photos
        """
        resp = self.session.get(f"{API_BASE}/getTokenInfo", params={
            "token": self.token,
        })
        return resp.json()

    def get_queue_estimate(self):
        """
        Estime le temps d'attente de la file d'attente

        Returns:
            dict: estimated_time_seconds
        """
        resp = self.session.get(f"{API_BASE}/getQueueEstimate")
        return resp.json()

    def create_project(self, project_name, num_photos, num_parts=1, filesize=0):
        """
        Crée un nouveau projet sur OpenScan Cloud

        Args:
            project_name: Nom du projet
            num_photos: Nombre de photos
            num_parts: Nombre de parties (défaut: 1)
            filesize: Taille totale en bytes (défaut: 0)

        Returns:
            dict: status, ulink (liens d'upload), credit
        """
        resp = self.session.get(f"{API_BASE}/createProject", params={
            "token": self.token,
            "project": project_name,
            "photos": num_photos,
            "parts": num_parts,
            "filesize": filesize,
        })
        return resp.json()

    def upload_photos(self, upload_links, photo_dir):
        """
        Upload les photos vers OpenScan Cloud via les liens Dropbox

        Args:
            upload_links: Liste des liens d'upload (de create_project)
            photo_dir: Dossier contenant les photos

        Returns:
            list: Résultats des uploads
        """
        results = []
        photos = sorted([
            f for f in os.listdir(photo_dir)
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))
        ])

        print(f"[Cloud] Upload de {len(photos)} photos...")

        for i, photo in enumerate(photos):
            if i >= len(upload_links):
                print(f"[Cloud] Attention: plus de liens d'upload disponibles")
                break

            filepath = os.path.join(photo_dir, photo)
            file_size = os.path.getsize(filepath)

            try:
                with open(filepath, 'rb') as f:
                    resp = requests.put(
                        upload_links[i],
                        data=f,
                        headers={"Content-Type": "image/jpeg"}
                    )

                if resp.status_code in (200, 201):
                    print(f"[Cloud] [{i+1}/{len(photos)}] {photo} OK")
                    results.append({"file": photo, "status": "ok"})
                else:
                    print(f"[Cloud] [{i+1}/{len(photos)}] {photo} ERREUR: {resp.status_code}")
                    results.append({"file": photo, "status": "error", "code": resp.status_code})

            except Exception as e:
                print(f"[Cloud] [{i+1}/{len(photos)}] {photo} ERREUR: {e}")
                results.append({"file": photo, "status": "error", "message": str(e)})

        return results

    def start_project(self, project_name):
        """
        Lance le traitement du projet

        Args:
            project_name: Nom du projet

        Returns:
            dict: status
        """
        resp = self.session.get(f"{API_BASE}/startProject", params={
            "token": self.token,
            "project": project_name,
        })
        return resp.json()

    def get_project_info(self, project_name):
        """
        Récupère les informations du projet (statut, lien de téléchargement)

        Args:
            project_name: Nom du projet

        Returns:
            dict: status, dlink, ulink
        """
        resp = self.session.get(f"{API_BASE}/getProjectInfo", params={
            "token": self.token,
            "project": project_name,
        })
        return resp.json()

    def process_scan(self, photo_dir, project_name=None, callback=None):
        """
        Processus complet: upload + lancement traitement

        Args:
            photo_dir: Dossier contenant les photos
            project_name: Nom du projet (défaut: nom du dossier)
            callback: Fonction appelée avec les messages de progression

        Returns:
            dict: Résultat du processus
        """
        if project_name is None:
            project_name = os.path.basename(photo_dir)

        def log(msg):
            print(msg)
            if callback:
                callback(msg)

        log(f"\n{'='*50}")
        log(f"OPENSCAN CLOUD - Traitement: {project_name}")
        log(f"{'='*50}")

        # Compter les photos
        photos = [
            f for f in os.listdir(photo_dir)
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))
        ]
        num_photos = len(photos)

        if num_photos == 0:
            log("[Cloud] Aucune photo trouvée!")
            return {"status": "error", "message": "Aucune photo"}

        log(f"[Cloud] {num_photos} photos à uploader")

        # Calculer la taille totale
        total_size = sum(
            os.path.getsize(os.path.join(photo_dir, f))
            for f in photos
        )
        log(f"[Cloud] Taille totale: {total_size / 1024 / 1024:.1f} MB")

        # Vérifier le crédit
        token_info = self.get_token_info()
        if "credit" in token_info:
            log(f"[Cloud] Crédit restant: {token_info['credit']}")

        # Créer le projet
        log("[Cloud] Création du projet...")
        result = self.create_project(
            project_name=project_name,
            num_photos=num_photos,
            filesize=total_size,
        )

        if result.get("status") != "created":
            log(f"[Cloud] Erreur création projet: {result}")
            return {"status": "error", "message": result}

        upload_links = result.get("ulink", [])
        log(f"[Cloud] Projet créé, {len(upload_links)} liens d'upload")

        # Upload les photos
        log("[Cloud] Upload des photos...")
        upload_results = self.upload_photos(upload_links, photo_dir)
        ok_count = sum(1 for r in upload_results if r["status"] == "ok")
        log(f"[Cloud] {ok_count}/{num_photos} photos uploadées")

        if ok_count == 0:
            log("[Cloud] Aucune photo uploadée!")
            return {"status": "error", "message": "Upload échoué"}

        # Lancer le traitement
        log("[Cloud] Lancement du traitement...")
        start_result = self.start_project(project_name)
        log(f"[Cloud] Statut: {start_result}")

        # Estimer le temps d'attente
        queue = self.get_queue_estimate()
        if "estimated_time_seconds" in queue:
            est = int(queue["estimated_time_seconds"])
            log(f"[Cloud] Temps estimé: {est // 60}min {est % 60}s")

        log(f"\n[Cloud] Traitement lancé!")
        log(f"[Cloud] Tu recevras un email avec le lien de téléchargement du modèle 3D")
        log(f"{'='*50}\n")

        return {
            "status": "processing",
            "project": project_name,
            "photos": ok_count,
            "estimated_time": queue.get("estimated_time_seconds", 0),
        }


def create_zip(photo_dir, output_path=None):
    """
    Crée un zip contenant toutes les photos

    Args:
        photo_dir: Dossier contenant les photos
        output_path: Chemin de sortie (défaut: photo_dir/scan.zip)

    Returns:
        str: Chemin du fichier zip
    """
    if output_path is None:
        output_path = os.path.join(photo_dir, "scan.zip")

    photos = [
        f for f in os.listdir(photo_dir)
        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))
    ]

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for photo in photos:
            filepath = os.path.join(photo_dir, photo)
            zf.write(filepath, photo)

    size = os.path.getsize(output_path)
    print(f"[Cloud] Zip créé: {output_path} ({size / 1024 / 1024:.1f} MB)")
    return output_path


if __name__ == "__main__":
    # Test
    cloud = OpenScanCloud()

    # Vérifier le crédit
    info = cloud.get_token_info()
    print(f"Info token: {info}")

    # Estimer le temps
    queue = cloud.get_queue_estimate()
    print(f"File d'attente: {queue}")
