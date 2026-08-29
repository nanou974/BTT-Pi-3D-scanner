/*
 * Firmware Arduino pour Scanner 3D
 * CNC Shield V3 + A4988 + Arduino Uno
 *
 * Protocol série (115200 baud):
 *   MX<steps>   - Déplacer l'axe X (plateau)
 *   MY<steps>   - Déplacer l'axe Y (bras caméra)
 *   HOME        - Retour à la position zéro
 *   STATUS      - Status des positions
 *   ENABLE      - Activer les moteurs
 *   DISABLE     - Désactiver les moteurs
 *   RESET       - Reset les positions à zéro
 *   POS         - Retourne les positions actuelles
 *   OK          - Test de connexion
 *   SPEED<val>  - Vitesse (microsecondes par pas, défaut: 500)
 *
 * Réponse: "OK" pour chaque commande, ou "ERR:<message>"
 *
 * Pinout CNC Shield V3:
 *   X.STEP → Pin 2,  X.DIR → Pin 5
 *   Y.STEP → Pin 3,  Y.DIR → Pin 6
 *   Z.STEP → Pin 4,  Z.DIR → Pin 7
 *   EN     → Pin 8
 */

// === Pins ===
#define X_STEP 2
#define X_DIR  5
#define Y_STEP 3
#define Y_DIR  6
#define Z_STEP 4
#define Z_DIR  7
#define EN_PIN 8

// === Variables ===
long posX = 0;
long posY = 0;
int stepDelay = 500;  // Microsecondes par pas (vitesse)
String inputBuffer = "";

void setup() {
  Serial.begin(115200);

  pinMode(X_STEP, OUTPUT);
  pinMode(X_DIR, OUTPUT);
  pinMode(Y_STEP, OUTPUT);
  pinMode(Y_DIR, OUTPUT);
  pinMode(Z_STEP, OUTPUT);
  pinMode(Z_DIR, OUTPUT);
  pinMode(EN_PIN, OUTPUT);

  digitalWrite(EN_PIN, HIGH);  // Moteurs désactivés par défaut
  digitalWrite(X_STEP, LOW);
  digitalWrite(X_DIR, LOW);
  digitalWrite(Y_STEP, LOW);
  digitalWrite(Y_DIR, LOW);

  Serial.println("SCANNER3D_RDY");
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (inputBuffer.length() > 0) {
        processCommand(inputBuffer);
        inputBuffer = "";
      }
    } else {
      inputBuffer += c;
    }
  }
}

void processCommand(String cmd) {
  cmd.trim();
  cmd.toUpperCase();

  if (cmd == "OK") {
    Serial.println("OK");
  }
  else if (cmd == "HOME") {
    homeMotors();
    Serial.println("OK");
  }
  else if (cmd == "STATUS") {
    Serial.print("POS X:");
    Serial.print(posX);
    Serial.print(" Y:");
    Serial.println(posY);
  }
  else if (cmd == "POS") {
    Serial.print(posX);
    Serial.print(",");
    Serial.println(posY);
  }
  else if (cmd == "ENABLE") {
    digitalWrite(EN_PIN, LOW);
    delay(10);
    Serial.println("OK");
  }
  else if (cmd == "DISABLE") {
    digitalWrite(EN_PIN, HIGH);
    Serial.println("OK");
  }
  else if (cmd == "RESET") {
    posX = 0;
    posY = 0;
    Serial.println("OK");
  }
  else if (cmd.startsWith("SPEED")) {
    int val = cmd.substring(5).toInt();
    if (val > 0 && val < 10000) {
      stepDelay = val;
      Serial.print("OK SPEED:");
      Serial.println(stepDelay);
    } else {
      Serial.println("ERR:SPEED_RANGE");
    }
  }
  else if (cmd.startsWith("MX")) {
    long steps = cmd.substring(2).toInt();
    moveAxis(X_STEP, X_DIR, steps, true);
    Serial.println("OK");
  }
  else if (cmd.startsWith("MY")) {
    long steps = cmd.substring(2).toInt();
    moveAxis(Y_STEP, Y_DIR, steps, true);
    Serial.println("OK");
  }
  else if (cmd.startsWith("MZ")) {
    long steps = cmd.substring(2).toInt();
    moveAxis(Z_STEP, Z_DIR, steps, true);
    Serial.println("OK");
  }
  else if (cmd.startsWith("CAL")) {
    // CALX ou CALZ: Calibration par bump
    // Déplace l'axe en position négative jusqu'à la butée
    char axis = cmd.charAt(3);
    long maxSteps = cmd.substring(4).toInt();
    if (maxSteps <= 0) maxSteps = 6400;  // Défaut: 1 tour à 1/16

    int stepPin, dirPin;
    if (axis == 'X') { stepPin = X_STEP; dirPin = X_DIR; }
    else if (axis == 'Z') { stepPin = Z_STEP; dirPin = Z_DIR; }
    else { Serial.println("ERR:AXIS"); return; }

    // Vitesse lente pour le calibrage
    int savedDelay = stepDelay;
    stepDelay = 800;  // Plus lent pour le bump

    // Déplacer en négatif (vers la butée)
    moveAxis(stepPin, dirPin, -maxSteps, false);

    stepDelay = savedDelay;

    // Reset la position
    if (axis == 'X') posX = 0;
    else posY = 0;

    Serial.println("OK");
  }
  else {
    Serial.print("ERR:UNKNOWN:");
    Serial.println(cmd);
  }
}

void moveAxis(int stepPin, int dirPin, long steps, bool updatePos) {
  // Activer les moteurs avant mouvement
  digitalWrite(EN_PIN, LOW);
  delay(5);

  if (steps > 0) {
    digitalWrite(dirPin, HIGH);
  } else {
    digitalWrite(dirPin, LOW);
    steps = -steps;
  }

  for (long i = 0; i < steps; i++) {
    digitalWrite(stepPin, HIGH);
    delayMicroseconds(stepDelay);
    digitalWrite(stepPin, LOW);
    delayMicroseconds(stepDelay);
  }

  if (updatePos) {
    if (stepPin == X_STEP) {
      posX += (steps > 0) ? steps : -steps;
    } else if (stepPin == Y_STEP) {
      posY += (steps > 0) ? steps : -steps;
    }
  }
}

void homeMotors() {
  // Retour au zéro logiciel (pas de switch physique)
  if (posX != 0) {
    moveAxis(X_STEP, X_DIR, -posX, true);
  }
  if (posY != 0) {
    moveAxis(Y_STEP, Y_DIR, -posY, true);
  }
  posX = 0;
  posY = 0;
}
