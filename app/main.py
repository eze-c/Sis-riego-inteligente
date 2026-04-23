import time
import json
import os
import logging
import serial
from dotenv import load_dotenv
from utils import conectar_serial, leer_humedad, enviar_comando_riego, verificar_umbral

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

ARCHIVO_DATOS = os.getenv('DATA_FILE', '/app/datos_riego.json')
INTERVALO_LECTURA = 2
MAX_HISTORIAL = 20

def guardar_datos(humedad, estado, historial):
    """
    Guarda el estado actual del sistema en un archivo JSON
    para que el dashboard pueda leerlo.

    Args:
        humedad (float): porcentaje de humedad actual.
        estado (str): estado del sistema ('OK', 'REGANDO', 'ERROR').
        historial (list): lista de lecturas anteriores.
    """
    datos = {
        'humedad_actual': humedad,
        'estado': estado,
        'historial': historial[-MAX_HISTORIAL:]
    }
    with open(ARCHIVO_DATOS, 'w') as f:
        json.dump(datos, f)

def main():
    """
    Función principal del sistema de riego.
    Se conecta al Arduino, lee la humedad cada 2 segundos
    y activa el riego automáticamente si es necesario.
    """
    logging.info("Iniciando sistema de riego...")

    ser = conectar_serial()
    if ser is None:
        logging.error("No se pudo conectar al Arduino. Verificá el puerto en .env")
        return

    umbral = int(os.getenv('HUMIDITY_THRESHOLD', 30))
    historial = []

    logging.info(f"Sistema iniciado. Umbral de riego: {umbral}%. Leyendo cada {INTERVALO_LECTURA} segundos...")

    while True:
        try:
            humedad = leer_humedad(ser)

            if humedad is not None:
                historial.append(humedad)

                if verificar_umbral(humedad, umbral):
                    enviar_comando_riego(ser)
                    estado = "REGANDO"
                    logging.warning(f"Humedad baja ({humedad}%) — activando riego")
                else:
                    estado = "OK"
                    logging.info(f"Humedad OK ({humedad}%)")

                guardar_datos(humedad, estado, historial)

            else:
                logging.error("Error leyendo humedad del sensor")
                guardar_datos(None, "ERROR", historial)

        except serial.SerialException:
            logging.error("Se perdió la conexión con el Arduino. Intentando reconectar...")
            ser = conectar_serial()

        time.sleep(INTERVALO_LECTURA)

if __name__ == "__main__":
    main()