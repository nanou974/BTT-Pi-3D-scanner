"""
Interface web pour le Scanner 3D
Utilise Flask pour créer une interface de contrôle à distance
"""

import os
import json
import threading
import cv2
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request, send_from_directory, Response
from scanner import Scanner3D
from camera import WebcamCapture
from config import WEB_INTERFACE


app = Flask(__name__)

# Instance globale du scanner
scanner = None
scan_thread = None

# Instance caméra dédiée au flux vidéo
video_camera = None


# === Template HTML ===
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scanner 3D - Contrôle</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #1a1a2e;
            color: #eee;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            text-align: center;
            padding: 30px 0;
            background: linear-gradient(135deg, #16213e, #0f3460);
            border-radius: 10px;
            margin-bottom: 30px;
        }
        h1 {
            font-size: 2.5em;
            color: #e94560;
        }
        .subtitle {
            color: #a0a0a0;
            margin-top: 10px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
        }
        .card {
            background: #16213e;
            border-radius: 10px;
            padding: 25px;
            border: 1px solid #0f3460;
        }
        .card h2 {
            color: #e94560;
            margin-bottom: 20px;
            font-size: 1.3em;
            border-bottom: 2px solid #0f3460;
            padding-bottom: 10px;
        }
        .btn {
            display: inline-block;
            padding: 12px 24px;
            margin: 5px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s;
        }
        .btn-primary {
            background: #e94560;
            color: white;
        }
        .btn-primary:hover {
            background: #ff6b6b;
        }
        .btn-secondary {
            background: #0f3460;
            color: white;
        }
        .btn-secondary:hover {
            background: #1a4a7a;
        }
        .btn-danger {
            background: #c0392b;
            color: white;
        }
        .btn-danger:hover {
            background: #e74c3c;
        }
        .btn:disabled {
            background: #555;
            cursor: not-allowed;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            color: #a0a0a0;
        }
        .form-group input, .form-group select {
            width: 100%;
            padding: 10px;
            border: 1px solid #0f3460;
            border-radius: 5px;
            background: #1a1a2e;
            color: #eee;
            font-size: 1em;
        }
        .status {
            padding: 15px;
            border-radius: 5px;
            margin-top: 15px;
        }
        .status-idle {
            background: #1a3a2e;
            border: 1px solid #27ae60;
        }
        .status-scanning {
            background: #3a2a1a;
            border: 1px solid #f39c12;
        }
        .status-error {
            background: #3a1a1a;
            border: 1px solid #e74c3c;
        }
        .progress {
            width: 100%;
            height: 20px;
            background: #1a1a2e;
            border-radius: 10px;
            overflow: hidden;
            margin: 15px 0;
        }
        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #e94560, #ff6b6b);
            transition: width 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8em;
        }
        .control-buttons {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 15px;
        }
        .motor-control {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        .motor-section {
            padding: 15px;
            background: #1a1a2e;
            border-radius: 5px;
        }
        .motor-section h3 {
            color: #e94560;
            margin-bottom: 10px;
            font-size: 1em;
        }
        .preview-container {
            text-align: center;
            margin-top: 15px;
        }
        .preview-container img {
            max-width: 100%;
            border-radius: 5px;
            border: 2px solid #0f3460;
        }
        .camera-full {
            width: 100%;
            margin-bottom: 20px;
        }
        .camera-full img {
            width: 100%;
            max-height: 500px;
            object-fit: contain;
            border-radius: 10px;
            border: 2px solid #0f3460;
            background: #0a0a15;
        }
        .camera-bar {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 10px;
        }
        .log {
            background: #0a0a15;
            border-radius: 5px;
            padding: 15px;
            max-height: 200px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 0.9em;
            margin-top: 15px;
        }
        .log-entry {
            margin: 5px 0;
            padding: 5px;
            border-bottom: 1px solid #16213e;
        }
        .log-time {
            color: #666;
        }
        @media (max-width: 768px) {
            .container { padding: 10px; }
            header h1 { font-size: 1.5em; }
            .grid { grid-template-columns: 1fr; }
            .motor-control { grid-template-columns: 1fr; }
            .camera-full img { max-height: 300px; }
            .btn { padding: 12px 16px; font-size: 1em; }
            .control-buttons { gap: 8px; }
            .control-buttons .btn { flex: 1; min-width: 0; }
            .card { padding: 15px; }
            .card h2 { font-size: 1.1em; }
            .motor-section { padding: 10px; }
            .log { max-height: 150px; font-size: 0.8em; }
            #cloud-scan-list div { padding: 6px 10px; font-size: 0.9em; }
        }
        @media (max-width: 480px) {
            header h1 { font-size: 1.2em; }
            header p { font-size: 0.8em; }
            .camera-full img { max-height: 220px; }
            .btn { padding: 10px 12px; font-size: 0.9em; }
            .control-buttons { flex-direction: column; }
            .control-buttons .btn { width: 100%; }
            .motor-section h3 { font-size: 0.9em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Scanner 3D</h1>
            <p class="subtitle">Interface de contrôle - BTT Pi v1.2</p>
            <div id="network-info" style="margin-top:8px; font-size:0.85em; color:#a0a0a0;">
                <span id="network-mode">Chargement...</span>
                <button class="btn btn-secondary" id="network-toggle" onclick="toggleNetwork()" style="padding:4px 10px; font-size:0.8em; margin-left:8px;">--</button>
            </div>
        </header>

        <!-- Caméra en grand en haut -->
        <div class="card camera-full">
            <h2>Aperçu caméra</h2>
            <img id="preview" src="/video_feed" alt="Aperçu caméra" onerror="this.src='data:image/svg+xml,<svg xmlns=\\'http://www.w3.org/2000/svg\\'/>'">
            <div class="camera-bar">
                <button class="btn btn-secondary" onclick="capturePhoto()">Capturer photo</button>
                <button class="btn btn-secondary" onclick="refreshPreview()">Rafraîchir</button>
            </div>
        </div>

        <!-- Contrôles en dessous -->
        <div class="grid">
            <!-- Statut -->
            <div class="card">
                <h2>Statut</h2>
                <div id="status" class="status status-idle">
                    <strong>État:</strong> <span id="status-text">En attente</span>
                </div>
                <div class="progress">
                    <div id="progress-bar" class="progress-bar" style="width: 0%">0%</div>
                </div>
                <p><strong>Photos:</strong> <span id="photo-count">0</span> / <span id="photo-total">0</span></p>
                <p><strong>Plateau:</strong> <span id="turntable-pos">0</span>°</p>
                <p><strong>Bras:</strong> <span id="arm-pos">0</span>°</p>
            </div>

            <!-- Configuration du scan -->
            <div class="card">
                <h2>Nouveau Scan</h2>
                <div class="form-group">
                    <label for="project-name">Nom du projet</label>
                    <input type="text" id="project-name" placeholder="Mon scan 3D">
                </div>
                <div class="form-group">
                    <label for="photos-per-rotation">Photos par rotation</label>
                    <input type="number" id="photos-per-rotation" value="36" min="4" max="360">
                </div>
                <div class="form-group">
                    <label for="arm-positions">Positions verticales</label>
                    <input type="number" id="arm-positions" value="5" min="1" max="20">
                </div>
                <div class="control-buttons">
                    <button class="btn btn-primary" id="start-btn" onclick="startScan()">Démarrer le scan</button>
                    <button class="btn btn-danger" onclick="stopScan()" id="stop-btn" disabled>Arrêter</button>
                </div>
            </div>

            <!-- Contrôle manuel des moteurs -->
            <div class="card">
                <h2>Contrôle manuel</h2>
                <div class="motor-control">
                    <div class="motor-section">
                        <h3>Plateau tournant</h3>
                        <div class="control-buttons">
                            <button class="btn btn-secondary" onclick="moveMotor('turntable', -90)">-90°</button>
                            <button class="btn btn-secondary" onclick="moveMotor('turntable', -45)">-45°</button>
                            <button class="btn btn-secondary" onclick="moveMotor('turntable', 45)">+45°</button>
                            <button class="btn btn-secondary" onclick="moveMotor('turntable', 90)">+90°</button>
                        </div>
                        <div class="control-buttons" style="margin-top: 10px;">
                            <button class="btn btn-secondary" onclick="homeMotor('turntable')">Home</button>
                        </div>
                    </div>
                    <div class="motor-section">
                        <h3>Bras caméra</h3>
                        <div class="control-buttons">
                            <button class="btn btn-secondary" onclick="moveMotor('arm', -45)">-45°</button>
                            <button class="btn btn-secondary" onclick="moveMotor('arm', -22.5)">-22.5°</button>
                            <button class="btn btn-secondary" onclick="moveMotor('arm', 22.5)">+22.5°</button>
                            <button class="btn btn-secondary" onclick="moveMotor('arm', 45)">+45°</button>
                        </div>
                        <div class="control-buttons" style="margin-top: 10px;">
                            <button class="btn btn-secondary" onclick="homeMotor('arm')">Home</button>
                        </div>
                    </div>
                </div>
                <div class="control-buttons" style="margin-top: 15px; justify-content: center;">
                    <button class="btn btn-secondary" onclick="disableMotors()">Désactiver moteurs</button>
                    <button class="btn btn-secondary" onclick="calibrate()">Calibration</button>
                </div>
            </div>

            <!-- OpenScan Cloud -->
            <div class="card" style="grid-column: 1 / -1;">
                <h2>OpenScan Cloud (Gratuit)</h2>
                <div class="form-group">
                    <label>Scans disponibles</label>
                    <div id="cloud-scan-list" style="max-height:200px; overflow-y:auto; border:1px solid #0f3460; border-radius:5px; background:#1a1a2e;">
                        <div style="padding:10px; color:#888;">Chargement...</div>
                    </div>
                </div>
                <div class="control-buttons" style="justify-content: center;">
                    <button class="btn btn-primary" onclick="uploadToCloud()">Uploader vers OpenScan Cloud</button>
                    <button class="btn btn-secondary" onclick="refreshScans()">Rafraîchir</button>
                </div>
                <div id="cloud-status" style="margin-top: 15px; padding: 10px; border-radius: 5px; display: none;"></div>
            </div>

            <!-- Logs -->
            <div class="card" style="grid-column: 1 / -1;">
                <h2>Journal</h2>
                <div id="log" class="log">
                    <div class="log-entry">
                        <span class="log-time">[Initialisation]</span>
                        Interface prête. En attente d'instructions...
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Mise à jour automatique du statut
        setInterval(updateStatus, 2000);

        function updateStatus() {
            fetch('/api/status')
                .then(r => r.json())
                .then(data => {
                    const scanning = data.is_scanning;
                    document.getElementById('status-text').textContent =
                        scanning ? 'Scan en cours...' : 'En attente';
                    document.getElementById('status').className =
                        'status ' + (scanning ? 'status-scanning' : 'status-idle');
                    document.getElementById('stop-btn').disabled = !scanning;
                    document.getElementById('start-btn').disabled = scanning;

                    if (data.current_scan) {
                        const photos = data.current_scan.photos_captured;
                        const total = data.current_scan.total_estimated;
                        document.getElementById('photo-count').textContent = photos;
                        document.getElementById('photo-total').textContent = total;

                        const percent = total > 0 ? (photos / total * 100) : 0;
                        document.getElementById('progress-bar').style.width = percent + '%';
                        document.getElementById('progress-bar').textContent = Math.round(percent) + '%';
                    }

                    document.getElementById('turntable-pos').textContent =
                        Math.round(data.motors.turntable_position / (200 * 16) * 360);
                    document.getElementById('arm-pos').textContent =
                        Math.round(data.motors.arm_position / (200 * 16) * 360);
                })
                .catch(err => console.error('Erreur statut:', err));
        }

        function addLog(message) {
            const log = document.getElementById('log');
            const time = new Date().toLocaleTimeString();
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            entry.innerHTML = `<span class="log-time">[${time}]</span> ${message}`;
            log.insertBefore(entry, log.firstChild);
        }

        // === Réseau ===
        function updateNetwork() {
            fetch('/api/network/mode')
                .then(r => r.json())
                .then(data => {
                    const modeEl = document.getElementById('network-mode');
                    const btn = document.getElementById('network-toggle');
                    if (data.mode === 'hotspot') {
                        modeEl.textContent = 'Hotspot : ' + data.hotspot_ssid + ' (' + data.ip + ')';
                        btn.textContent = 'Mode client';
                        btn.className = 'btn btn-danger';
                    } else {
                        modeEl.textContent = 'WiFi : ' + (data.ssid || '...' ) + ' (' + data.ip + ')';
                        btn.textContent = 'Mode hotspot';
                        btn.className = 'btn btn-primary';
                    }
                })
                .catch(() => {
                    document.getElementById('network-mode').textContent = 'Réseau inconnu';
                });
        }

        function toggleNetwork() {
            const btn = document.getElementById('network-toggle');
            const isHotspot = btn.className.includes('btn-danger');
            const url = isHotspot ? '/api/network/client' : '/api/network/hotspot';

            if (!confirm(isHotspot ?
                'Revenir en mode client WiFi ?' :
                'Activer le hotspot ? Tu seras déconnecté et devras te reconnecter à Scanner3D.')) return;

            fetch(url, { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    addLog(data.message);
                    setTimeout(updateNetwork, 3000);
                })
                .catch(err => addLog('Erreur réseau: ' + err));
        }

        setInterval(updateNetwork, 10000);
        updateNetwork();

        function startScan() {
            const data = {
                project_name: document.getElementById('project-name').value || undefined,
                photos_per_rotation: parseInt(document.getElementById('photos-per-rotation').value),
                arm_positions: parseInt(document.getElementById('arm-positions').value)
            };

            fetch('/api/scan/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            })
            .then(r => r.json())
            .then(result => {
                addLog('Scan démarré: ' + result.scan_id);
                // Démarrer l'exécution
                fetch('/api/scan/execute', {method: 'POST'});
            })
            .catch(err => addLog('Erreur: ' + err));
        }

        function stopScan() {
            fetch('/api/scan/stop', {method: 'POST'})
                .then(r => r.json())
                .then(result => addLog('Scan arrêté'))
                .catch(err => addLog('Erreur: ' + err));
        }

        function moveMotor(motor, angle) {
            fetch(`/api/motor/move?motor=${motor}&angle=${angle}`, {method: 'POST'})
                .then(r => r.json())
                .then(result => addLog(`Déplacement ${motor}: ${angle}°`))
                .catch(err => addLog('Erreur: ' + err));
        }

        function homeMotor(motor) {
            fetch(`/api/motor/home?motor=${motor}`, {method: 'POST'})
                .then(r => r.json())
                .then(result => addLog(`Home ${motor}`))
                .catch(err => addLog('Erreur: ' + err));
        }

        function disableMotors() {
            fetch('/api/motor/disable', {method: 'POST'})
                .then(r => r.json())
                .then(result => addLog('Moteurs désactivés'))
                .catch(err => addLog('Erreur: ' + err));
        }

        function calibrate() {
            addLog('Début de la calibration...');
            fetch('/api/calibrate', {method: 'POST'})
                .then(r => r.json())
                .then(result => addLog('Calibration terminée'))
                .catch(err => addLog('Erreur: ' + err));
        }

        function capturePhoto() {
            fetch('/api/camera/capture', {method: 'POST'})
                .then(r => r.json())
                .then(result => addLog('Photo capturée: ' + result.file))
                .catch(err => addLog('Erreur: ' + err));
        }

        function refreshPreview() {
            document.getElementById('preview').src = '/video_feed?' + Date.now();
        }

        // === OpenScan Cloud ===
        let selectedScan = null;

        function refreshScans() {
            fetch('/api/files')
                .then(r => r.json())
                .then(data => {
                    const list = document.getElementById('cloud-scan-list');
                    list.innerHTML = '';
                    if (data.scans.length === 0) {
                        list.innerHTML = '<div style="padding:10px; color:#888;">Aucun scan disponible</div>';
                    } else {
                        data.scans.forEach(scan => {
                            const item = document.createElement('div');
                            item.style.cssText = 'display:flex; align-items:center; justify-content:space-between; padding:8px 12px; border-bottom:1px solid #0f3460; cursor:pointer;';
                            item.innerHTML = `
                                <span style="flex:1;">${scan.name} (${scan.photos} photos)</span>
                                <button class="btn btn-danger" style="padding:4px 8px; font-size:12px; margin-left:10px;" onclick="deleteScan('${scan.name}', event)">✕</button>
                            `;
                            item.onclick = (e) => {
                                if (e.target.tagName === 'BUTTON') return;
                                selectedScan = scan.name;
                                list.querySelectorAll('div').forEach(d => d.style.background = '');
                                item.style.background = '#0f3460';
                                addLog('Scan sélectionné: ' + scan.name);
                            };
                            list.appendChild(item);
                        });
                    }
                })
                .catch(err => addLog('Erreur chargement scans: ' + err));
        }

        function deleteScan(name, event) {
            event.stopPropagation();
            if (!confirm('Supprimer le scan "' + name + '" ?')) return;

            fetch('/api/files/' + encodeURIComponent(name), { method: 'DELETE' })
                .then(r => r.json())
                .then(data => {
                    if (data.ok) {
                        addLog('Scan supprimé: ' + name);
                        if (selectedScan === name) selectedScan = null;
                        refreshScans();
                    } else {
                        addLog('Erreur: ' + data.error);
                    }
                })
                .catch(err => addLog('Erreur suppression: ' + err));
        }

        function uploadToCloud() {
            if (!selectedScan) {
                addLog('Sélectionne un scan à uploader');
                return;
            }

            const statusDiv = document.getElementById('cloud-status');
            statusDiv.style.display = 'block';
            statusDiv.style.background = '#3a2a1a';
            statusDiv.style.border = '1px solid #f39c12';
            statusDiv.innerHTML = 'Upload en cours...';

            addLog('Upload vers OpenScan Cloud: ' + selectedScan);

            fetch('/api/cloud/upload', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({scan: selectedScan})
            })
            .then(r => r.json())
            .then(result => {
                if (result.status === 'processing') {
                    statusDiv.style.background = '#1a3a2e';
                    statusDiv.style.border = '1px solid #27ae60';
                    statusDiv.innerHTML = 'Traitement lancé ! ' + result.photos + ' photos uploadées. ' +
                        'Tu recevras un email avec le lien de téléchargement.';
                    addLog('OpenScan Cloud: traitement lancé pour ' + selectedScan);
                } else {
                    statusDiv.style.background = '#3a1a1a';
                    statusDiv.style.border = '1px solid #e74c3c';
                    statusDiv.innerHTML = 'Erreur: ' + (result.message || 'Inconnue');
                    addLog('Erreur OpenScan Cloud: ' + (result.message || 'Inconnue'));
                }
            })
            .catch(err => {
                statusDiv.style.background = '#3a1a1a';
                statusDiv.style.border = '1px solid #e74c3c';
                statusDiv.innerHTML = 'Erreur réseau';
                addLog('Erreur upload: ' + err);
            });
        }

        // Charger la liste des scans au démarrage
        refreshScans();
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """Page principale"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/video_feed')
def video_feed():
    """Flux vidéo de la webcam"""
    global video_camera

    # Utiliser une caméra dédiée pour le flux vidéo
    if video_camera is None or not video_camera.is_opened:
        video_camera = WebcamCapture()
        if not video_camera.open():
            def error_frame():
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n'
                       b'\xff\xd8\xff\xe0\x00\x10JFIF\x00'  # Header JPEG minimal
                       b'\xff\xd9')
            return Response(error_frame(),
                            mimetype='multipart/x-mixed-replace; boundary=frame')

    def generate():
        while True:
            frame = video_camera.capture_frame()
            if frame is None:
                break

            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/status')
def api_status():
    """API: Statut du scanner"""
    if scanner:
        return jsonify(scanner.get_status())
    return jsonify({"error": "Scanner non initialisé"}), 500


@app.route('/api/network/mode')
def api_network_mode():
    """API: Vérifier le mode réseau actuel"""
    import subprocess
    try:
        # Vérifier si hostapd tourne
        result = subprocess.run(['systemctl', 'is-active', 'hostapd'],
                                capture_output=True, text=True)
        hotspot_active = result.stdout.strip() == 'active'

        # Obtenir l'IP actuelle
        ip_result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
        ip = ip_result.stdout.strip().split()[0] if ip_result.stdout.strip() else 'N/A'

        # Obtenir le SSID connecté (mode client)
        ssid = ''
        if not hotspot_active:
            ssid_result = subprocess.run(['iwgetid', '-r'], capture_output=True, text=True)
            ssid = ssid_result.stdout.strip()

        return jsonify({
            "mode": "hotspot" if hotspot_active else "client",
            "ip": ip,
            "ssid": ssid,
            "hotspot_ssid": "Scanner3D"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/network/hotspot', methods=['POST'])
def api_network_hotspot():
    """API: Activer le mode hotspot"""
    import subprocess
    script = os.path.join(os.path.dirname(__file__), 'hotspot_on.sh')
    try:
        subprocess.Popen(['bash', script])
        return jsonify({"ok": True, "message": "Hotspot en cours d'activation... Reconnecte-toi à Scanner3D"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/network/client', methods=['POST'])
def api_network_client():
    """API: Revenir en mode client"""
    import subprocess
    script = os.path.join(os.path.dirname(__file__), 'hotspot_off.sh')
    try:
        subprocess.Popen(['bash', script])
        return jsonify({"ok": True, "message": "Mode client activé... Reconnecte-toi à ton WiFi"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/scan/start', methods=['POST'])
def api_scan_start():
    """API: Démarrer un scan"""
    if not scanner:
        return jsonify({"error": "Scanner non initialisé"}), 500

    data = request.get_json() or {}
    scan_id = scanner.start_scan(
        photos_per_rotation=data.get('photos_per_rotation'),
        arm_positions=data.get('arm_positions'),
        project_name=data.get('project_name'),
    )

    return jsonify({"scan_id": scan_id, "status": "démarré"})


@app.route('/api/scan/execute', methods=['POST'])
def api_scan_execute():
    """API: Exécuter le scan (en arrière-plan)"""
    if not scanner or not scanner.is_scanning:
        return jsonify({"error": "Aucun scan en cours"}), 400

    def run_scan():
        scanner.execute_scan()

    global scan_thread
    scan_thread = threading.Thread(target=run_scan, daemon=True)
    scan_thread.start()

    return jsonify({"status": "exécution lancée"})


@app.route('/api/scan/stop', methods=['POST'])
def api_scan_stop():
    """API: Arrêter le scan"""
    if scanner and scanner.is_scanning:
        scanner.is_scanning = False
        return jsonify({"status": "arrêté"})
    return jsonify({"error": "Aucun scan en cours"}), 400


@app.route('/api/motor/move', methods=['POST'])
def api_motor_move():
    """API: Déplacer un moteur"""
    if not scanner:
        return jsonify({"error": "Scanner non initialisé"}), 500

    motor = request.args.get('motor', 'turntable')
    angle = float(request.args.get('angle', 0))

    if motor == 'turntable':
        scanner.motors.turntable.rotate_absolute(angle)
    elif motor == 'arm':
        scanner.motors.camera_arm.rotate_absolute(angle)
    else:
        return jsonify({"error": "Moteur inconnu"}), 400

    return jsonify({"motor": motor, "angle": angle, "status": "ok"})


@app.route('/api/motor/home', methods=['POST'])
def api_motor_home():
    """API: Retour à la position zéro"""
    if not scanner:
        return jsonify({"error": "Scanner non initialisé"}), 500

    motor = request.args.get('motor', 'turntable')

    if motor == 'turntable':
        scanner.motors.turntable.home()
    elif motor == 'arm':
        scanner.motors.camera_arm.home()
    else:
        return jsonify({"error": "Moteur inconnu"}), 400

    return jsonify({"motor": motor, "status": "home"})


@app.route('/api/motor/disable', methods=['POST'])
def api_motor_disable():
    """API: Désactiver les moteurs"""
    if scanner:
        scanner.motors.disable_all()
        return jsonify({"status": "désactivé"})
    return jsonify({"error": "Scanner non initialisé"}), 500


@app.route('/api/calibrate', methods=['POST'])
def api_calibrate():
    """API: Calibration"""
    if not scanner:
        return jsonify({"error": "Scanner non initialisé"}), 500

    def run_calibration():
        scanner.calibrate()

    global scan_thread
    scan_thread = threading.Thread(target=run_calibration, daemon=True)
    scan_thread.start()

    return jsonify({"status": "calibration lancée"})


@app.route('/api/camera/capture', methods=['POST'])
def api_camera_capture():
    """API: Capturer une photo"""
    if not scanner:
        return jsonify({"error": "Scanner non initialisé"}), 500

    filepath = scanner.camera.capture_and_save(subdir="manual")
    return jsonify({"file": filepath, "status": "ok"})


@app.route('/api/files')
def api_files():
    """API: Lister les fichiers de scan"""
    captures_dir = scanner.camera.output_dir if scanner else "captures"

    if not os.path.exists(captures_dir):
        return jsonify({"scans": []})

    scans = []
    for item in os.listdir(captures_dir):
        item_path = os.path.join(captures_dir, item)
        if os.path.isdir(item_path):
            photos = len([f for f in os.listdir(item_path) if f.endswith('.jpg')])
            scans.append({"name": item, "photos": photos})

    return jsonify({"scans": scans})


@app.route('/api/files/<path:filename>', methods=['DELETE'])
def api_delete_file(filename):
    """API: Supprimer un scan"""
    import shutil
    captures_dir = scanner.camera.output_dir if scanner else "captures"
    scan_dir = os.path.join(captures_dir, filename)

    if not os.path.exists(scan_dir):
        return jsonify({"error": "Scan non trouvé"}), 404

    try:
        shutil.rmtree(scan_dir)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/files/<path:filename>')
def api_file(filename):
    """API: Télécharger un fichier"""
    captures_dir = scanner.camera.output_dir if scanner else "captures"
    return send_from_directory(captures_dir, filename)


@app.route('/api/cloud/upload', methods=['POST'])
def api_cloud_upload():
    """API: Upload vers OpenScan Cloud"""
    data = request.get_json() or {}
    scan_name = data.get("scan")

    if not scan_name:
        return jsonify({"error": "Nom de scan manquant"}), 400

    captures_dir = scanner.camera.output_dir if scanner else "captures"
    scan_dir = os.path.join(captures_dir, scan_name)

    if not os.path.isdir(scan_dir):
        return jsonify({"error": f"Scan '{scan_name}' introuvable"}), 404

    try:
        from openscan_cloud import OpenScanCloud
        cloud = OpenScanCloud()

        result = cloud.process_scan(scan_dir, project_name=scan_name)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def create_app():
    """Crée et configure l'application Flask"""
    global scanner

    print("=== Démarrage du serveur web ===")
    scanner = Scanner3D()
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(
        host=WEB_INTERFACE["host"],
        port=WEB_INTERFACE["port"],
        debug=False,
        threaded=True
    )
