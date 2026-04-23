import serial
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def conectar_serial():
    """
    Establece la conexión con el Arduino por puerto serial.
    Lee el puerto y velocidad desde las variables de entorno.

    Returns:
        serial.Serial: objeto de conexión si tuvo éxito.
        None: si no pudo conectar.
    """
    puerto = os.getenv('ARDUINO_PORT', '/dev/ttyUSB0')
    baud = int(os.getenv('SERIAL_BAUD', 9600))
    try:
        ser = serial.Serial(puerto, baud, timeout=1)
        logging.info(f"Conectado al Arduino en {puerto}")
        return ser
    except serial.SerialException as e:
        logging.error(f"Error conectando al serial: {e}")
        return None

def leer_humedad(ser):
    """
    Solicita la humedad actual al Arduino enviando el comando GET_HUMIDITY.

    Args:
        ser (serial.Serial): objeto de conexión serial activo.

    Returns:
        float: porcentaje de humedad entre 0 y 100.
        None: si hubo error de lectura o no hay conexión.
    """
    if ser is None:
        return None
    try:
        ser.write(b'GET_HUMIDITY\n')
        respuesta = ser.readline().decode().strip()
        return float(respuesta) if respuesta else None
    except (ValueError, serial.SerialException) as e:
        logging.error(f"Error leyendo humedad: {e}")
        return None

def enviar_comando_riego(ser):
    """
    Envía el comando WATER al Arduino para activar el relé y la bomba.

    Args:
        ser (serial.Serial): objeto de conexión serial activo.

    Returns:
        bool: True si el comando se envió correctamente, False si hubo error.
    """
    if ser is None:
        return False
    try:
        ser.write(b'WATER\n')
        logging.info("Comando de riego enviado al Arduino")
        return True
    except serial.SerialException as e:
        logging.error(f"Error enviando comando de riego: {e}")
        return False

def verificar_umbral(humedad, umbral=30):
    """
    Verifica si la humedad está por debajo del umbral definido.

    Args:
        humedad (float): valor de humedad actual en porcentaje.
        umbral (int): porcentaje mínimo aceptable. Por defecto 30.

    Returns:
        bool: True si hay que regar, False si no es necesario.
    """
    return humedad < umbral if humedad is not None else False

def formatear_porcentaje(valor):
    """
    Formatea un valor numérico como string de porcentaje.

    Args:
        valor (float): valor a formatear.

    Returns:
        str: valor formateado como '64.0%' o 'N/A' si es None.
    """
    return f"{valor:.1f}%" if valor is not None else "N/A"