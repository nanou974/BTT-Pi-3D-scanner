"""
Script de test pour vérifier le matériel du Scanner 3D
Vérifie: GPIO, moteurs, webcam
"""

import sys
import time


def test_gpio():
    """Test des GPIO"""
    print("=" * 50)
    print("TEST GPIO")
    print("=" * 50)

    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Broches à tester
        test_pins = [17, 27, 22, 23, 24, 25]

        for pin in test_pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(pin, GPIO.LOW)
            time.sleep(0.1)
            print(f"  GPIO {pin}: OK")

        GPIO.cleanup()
        print("\n✅ GPIO: Tous les tests passés\n")
        return True

    except ImportError:
        print("⚠️  RPi.GPIO non disponible (pas sur un Raspberry Pi?)")
        print("   Test GPIO ignoré\n")
        return False
    except Exception as e:
        print(f"❌ Erreur GPIO: {e}\n")
        return False


def test_stepper():
    """Test des moteurs pas à pas"""
    print("=" * 50)
    print("TEST MOTEURS PAS À PAS")
    print("=" * 50)

    try:
        from stepper import ScannerMotors

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

        motors.cleanup()
        print("\n✅ Moteurs: Tous les tests passés\n")
        return True

    except ImportError:
        print("⚠️  Module stepper.py non trouvé")
        print("   Test moteurs ignoré\n")
        return False
    except Exception as e:
        print(f"❌ Erreur moteurs: {e}\n")
        return False


def test_camera():
    """Test de la webcam"""
    print("=" * 50)
    print("TEST WEBCAM")
    print("=" * 50)

    try:
        import cv2
        from camera import WebcamCapture

        cam = WebcamCapture()

        if cam.open():
            info = cam.get_camera_info()
            print(f"  Device: {info['device_id']}")
            print(f"  Résolution: {info['resolution']}")
            print(f"  FPS: {info['fps']}")

            print("\nTest: Capture d'une image")
            filepath = cam.capture_and_save(subdir="test")
            if filepath:
                print(f"  Image sauvegardée: {filepath}")

            cam.close()
            print("\n✅ Webcam: Tous les tests passés\n")
            return True
        else:
            print("❌ Impossible d'ouvrir la webcam\n")
            return False

    except ImportError:
        print("⚠️  opencv-python non installé")
        print("   Installez avec: pip3 install opencv-python")
        print("   Test webcam ignoré\n")
        return False
    except Exception as e:
        print(f"❌ Erreur webcam: {e}\n")
        return False


def test_web_server():
    """Test du serveur web"""
    print("=" * 50)
    print("TEST SERVEUR WEB")
    print("=" * 50)

    try:
        from flask import Flask
        print("  Flask: OK")

        # Test import web_app
        sys.path.insert(0, '.')
        from web_app import app
        print("  web_app: OK")

        print("\n✅ Serveur web: prêt\n")
        return True

    except ImportError:
        print("⚠️  Flask non installé")
        print("   Installez avec: pip3 install flask")
        print("   Test serveur web ignoré\n")
        return False
    except Exception as e:
        print(f"❌ Erreur serveur web: {e}\n")
        return False


def main():
    """Exécute tous les tests"""
    print("\n" + "=" * 50)
    print("   DIAGNOSTIC DU SCANNER 3D")
    print("=" * 50 + "\n")

    results = {
        "GPIO": test_gpio(),
        "Moteurs": test_stepper(),
        "Webcam": test_camera(),
        "Serveur Web": test_web_server(),
    }

    # Résumé
    print("\n" + "=" * 50)
    print("   RÉSUMÉ DES TESTS")
    print("=" * 50 + "\n")

    all_passed = True
    for name, passed in results.items():
        status = "✅ OK" if passed else "❌ ÉCHEC"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    print()

    if all_passed:
        print("🎉 Tous les tests sont passés!")
        print("   Vous pouvez lancer le scanner avec: python3 web_app.py")
    else:
        print("⚠️  Certains tests ont échoué.")
        print("   Vérifiez les messages d'erreur ci-dessus.")

    print()


if __name__ == "__main__":
    main()
