#define PIN_SENSOR A0
#define PIN_RELE 7

#define TIEMPO_RIEGO 5000  // 5 segundos de riego

void setup() {
  Serial.begin(9600);
  pinMode(PIN_RELE, OUTPUT);
  digitalWrite(PIN_RELE, HIGH);  // Relé apagado al inicio
  Serial.println("Sistema de Riego Listo");
}

void loop() {
  if (Serial.available() > 0) {
    String comando = Serial.readStringUntil('\n');
    comando.trim();  // Quita espacios y saltos de línea
    
    if (comando == "GET_HUMIDITY") {
      int humedad_raw = analogRead(PIN_SENSOR);
      int humedad_pct = map(humedad_raw, 1023, 0, 0, 100);
      Serial.println(humedad_pct);  // Responde con %
    } else if (comando == "WATER") {
      regar();  // Función para activar riego
    }
  }
  delay(100);  //delay para no saturar
}

void regar() {
  digitalWrite(PIN_RELE, LOW);
  Serial.println("REGANDO");
  
  unsigned long inicio = millis();
  
  while (millis() - inicio < TIEMPO_RIEGO) {
    int humedad_raw = analogRead(PIN_SENSOR);
    int humedad_pct = map(humedad_raw, 1023, 0, 0, 100);
    
    if (humedad_pct >= 50) {
      break;
    }
    delay(500);
  }
  
  digitalWrite(PIN_RELE, HIGH);
  Serial.println("RIEGO_TERMINADO");
}