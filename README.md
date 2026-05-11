# 💧 Sistema de Riego Inteligente

Sistema automatizado de riego que monitorea la humedad del suelo en tiempo real y activa una bomba de agua cuando es necesario. Desarrollado con Arduino, Python y Docker para Prácticas Profesionalizantes 3.

---

## 🎯 ¿Qué hace?

Lee la humedad del suelo cada 2 segundos usando un sensor enterrado, y si el valor cae por debajo del umbral configurado, manda una señal al Arduino para encender la bomba. Cuando el suelo vuelve a estar húmedo, la bomba se apaga sola. Todo esto sin que el usuario tenga que hacer nada.

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────┐
│               Sensor de Humedad (Suelo)             │
└──────────────────────┬──────────────────────────────┘
                       │ Pin analógico A0
                       ▼
┌─────────────────────────────────────────────────────┐
│    Arduino Uno                                      │
│  - Lee el sensor cuando Python lo pide              │
│  - Controla el relé por pin digital 7               │
│  - Protocolo serial: GET_HUMIDITY / WATER           │
└──────────────────────┬──────────────────────────────┘
                       │ USB Serial (9600 baudios)
                       ▼
┌─────────────────────────────────────────────────────┐
│  Docker Container (Python + Streamlit)              │
│                                                     │
│  main.py ── Lógica principal                        │
│    - Pide humedad al Arduino cada 2 segundos        │
│    - Decide si regar según el umbral                │
│    - Guarda los datos en datos_riego.json           │
│                                                     │
│  dashboard.py ── Interfaz web                       │
│    - Lee datos_riego.json                           │
│    - Muestra humedad actual y estado                │
│    - Muestra historial en gráfico                   │
└──────────────────────┬──────────────────────────────┘
                       │ Señal digital
                       ▼
┌─────────────────────────────────────────────────────┐
│  Módulo Relé → Bomba de Agua                        │
│  - Relé abre/cierra el circuito de las pilas        │
│  - Bomba riega hasta que la humedad supere el 50%   │
└─────────────────────────────────────────────────────┘
```

---

## 📁 Estructura del Proyecto

```
Riego-/
├── arduino/
│   └── riego/
│       └── riego.ino              # Código del microcontrolador
├── app/
│   ├── main.py                    # Lógica principal (lectura y control)
│   ├── dashboard.py               # Interfaz web con Streamlit
│   └── utils.py                   # Funciones de comunicación serial
├── .env                           # Variables de entorno (no se sube a Git)
├── .env.example                   # Plantilla de configuración
├── .gitignore
├── docker-compose.yml             # Orquestación del contenedor
├── Dockerfile                     # Imagen Docker de la aplicación
├── requirements.txt               # Dependencias Python
└── README.md
```

---

## ⚙️ El Circuito

### Componentes

| Componente | Función |
|-----------|---------|
| Arduino Uno | Microcontrolador central |
| Sensor YL-69 | Mide la humedad del suelo |
| Módulo Relé 5V | Controla el encendido de la bomba |
| Bomba sumergible 5V | Bombea el agua hacia el limonero |
| Protoboard | Conexión de componentes |

### Conexiones

**Sensor YL-69 → Arduino:**
```
VCC  →  5V
GND  →  GND
AO   →  A0 (entrada analógica)
```

**Módulo Relé → Arduino:**
```
VCC  →  5V
GND  →  GND
IN   →  Pin 7 (salida digital)
```

**Bomba → Relé → Pilas:**
```
Pilas (+)            →  COM del relé
NO del relé          →  cable rojo de la bomba (+)
cable negro bomba(-) →  Pilas (-)
```

### ¿Por qué un relé?

El Arduino maneja 5V con muy poca corriente — no alcanza para alimentar la bomba directamente. El relé actúa como interruptor electrónico: recibe la señal de bajo voltaje del Arduino y cierra el circuito de mayor potencia que viene de las pilas. El Arduino nunca toca la corriente de la bomba.

### ¿Por qué el pin A0 es analógico?

Los pines digitales solo leen 0 o 1. El pin analógico A0 lee valores entre 0 y 1023, lo que permite saber el porcentaje exacto de humedad en cualquier punto (32%, 67%, 85%, etc.) y no solo "seco" o "húmedo".

---

## 💻 El Código

### `arduino/riego/riego.ino`

El Arduino no decide cuándo regar — espera los comandos que le manda Python por el puerto serial.

**Constantes:**
```cpp
#define PIN_SENSOR A0        // Pin analógico del sensor
#define PIN_RELE 7           // Pin digital del relé
#define TIEMPO_RIEGO 5000    // Tiempo máximo de riego (5 segundos)
```

**`setup()`** — se ejecuta una vez al arrancar:
- Abre la comunicación serial a 9600 baudios
- Configura el pin del relé como salida
- Apaga el relé (`HIGH` = apagado en este módulo)

**`loop()`** — corre infinitamente:
- Escucha si Python mandó algún comando
- `GET_HUMIDITY`: lee el sensor, convierte el valor a porcentaje con `map()` y lo responde
- `WATER`: llama a la función `regar()`

**`regar()`:**
- Activa el relé (pin 7 → `LOW`, bomba enciende)
- Monitorea la humedad cada 500ms mientras riega
- Corta el riego si la humedad supera el 50% **o** si pasaron 5 segundos
- Apaga el relé y avisa por serial: `RIEGO_TERMINADO`

**¿Por qué `millis()` en vez de `delay()`?**

`delay()` congela el Arduino — no puede leer el sensor ni escuchar comandos mientras cuenta el tiempo. `millis()` devuelve los milisegundos transcurridos desde que arrancó, sin bloquear nada. Así la función `regar()` puede chequear la humedad mientras la bomba está andando.

---

### `app/utils.py`

Funciones de comunicación con el Arduino, separadas en su propio archivo para no repetir código entre `main.py` y `dashboard.py`.

**`conectar_serial()`**
Lee el puerto y la velocidad del `.env` y abre la conexión. Si falla (por ejemplo, el Arduino no está enchufado), devuelve `None` en lugar de tirar una excepción.

**`leer_humedad(ser)`**
Manda `GET_HUMIDITY\n` al Arduino y espera la respuesta. Convierte el texto recibido a `float`. Si hay cualquier error de lectura devuelve `None`.

**`enviar_comando_riego(ser)`**
Manda `WATER\n` al Arduino. Devuelve `True` si salió bien, `False` si hubo error.

**`verificar_umbral(humedad, umbral)`**
Compara la humedad actual con el umbral. Si la humedad está por debajo, hay que regar.

---

### `app/main.py`

El motor del sistema. Corre en un loop infinito dentro del contenedor Docker.

**Ciclo cada 2 segundos:**
1. Pide la humedad al Arduino con `GET_HUMIDITY`
2. Si la humedad está por debajo del umbral → manda `WATER`
3. Guarda humedad, estado e historial en `datos_riego.json`
4. El dashboard lee ese archivo y actualiza la interfaz

**Manejo de errores:**
- Si la lectura falla → guarda estado `ERROR` en el JSON y sigue intentando
- Si el Arduino se desconecta → llama a `conectar_serial()` para reconectarse

**¿Por qué un archivo JSON como canal de comunicación?**

`main.py` y `dashboard.py` corren como procesos separados (así lo define el `CMD` del Dockerfile). El JSON es la forma más simple de que se pasen datos: `main.py` escribe, `dashboard.py` lee. De paso, evita que ambos compitan por el puerto serial al mismo tiempo.

---

### `app/dashboard.py`

Interfaz web construida con Streamlit. Lee `datos_riego.json` y muestra todo en pantalla.

**Qué muestra:**
- Humedad actual en porcentaje
- Estado del sistema con colores (verde = OK, amarillo = regando, rojo = error)
- Gráfico de línea con el historial de las últimas 20 lecturas
- Línea roja en el gráfico marcando el umbral de riego
- Hora de la última actualización
- Botón para refrescar manualmente

**¿Por qué Streamlit y no Flask?**

Streamlit permite hacer dashboards con Python puro, sin HTML, CSS ni JavaScript. Para visualizar datos en tiempo real es mucho más rápido de armar y más que suficiente para este caso.

---

### `Dockerfile`

```dockerfile
FROM python:3.9-slim          # imagen base liviana
WORKDIR /app
COPY requirements.txt .       # primero las dependencias (aprovecha cache de Docker)
RUN pip install --no-cache-dir -r requirements.txt
COPY . .                      # después el resto del código
EXPOSE 8501                   # puerto de Streamlit
CMD ["sh", "-c", "python app/main.py & streamlit run app/dashboard.py --server.port 8501 --server.address 0.0.0.0"]
```

---

### `docker-compose.yml`

```yaml
services:
  app:
    build: .
    ports:
      - "8501:8501"                       # dashboard accesible desde el navegador
    devices:
      - "${ARDUINO_PORT}:/dev/ttyUSB1"   # acceso al puerto USB del Arduino
    env_file:
      - .env
    volumes:
      - .:/app                            # cambios en el código sin rebuild
    restart: unless-stopped
```

**¿Por qué `${ARDUINO_PORT}` y no el puerto fijo?**

El nombre del puerto USB varía según el sistema (`/dev/ttyUSB0`, `/dev/ttyUSB1`, `/dev/ttyACM0`). En este proyecto se usa `/dev/ttyUSB1` por defecto (está en el `.env`). Cambiarlo en el `.env` alcanza — no hace falta tocar el `docker-compose.yml`.

---

### `.env`

```env
ARDUINO_PORT=/dev/ttyUSB1       # puerto USB donde está el Arduino
HUMIDITY_THRESHOLD=30           # umbral mínimo de humedad (%)
SERIAL_BAUD=9600                # velocidad de comunicación serial
DATA_FILE=/app/datos_riego.json # ruta del archivo de datos compartido
```

---

## 🔄 Flujo Completo

```
1.  El sensor enterrado mide la resistencia eléctrica del suelo
2.  Arduino convierte el valor analógico a porcentaje (0-100%)
3.  main.py manda GET_HUMIDITY cada 2 segundos
4.  Arduino responde con el porcentaje
5.  main.py compara con el umbral del .env
6.  Si humedad < umbral → manda WATER al Arduino
7.  Arduino activa el relé (pin 7 → LOW)
8.  Relé cierra el circuito → bomba enciende
9.  Bomba riega el limonero
10. Sensor detecta que la humedad sube
11. Arduino corta el riego (humedad ≥ 50% o pasaron 5 segundos)
12. main.py guarda los datos en datos_riego.json
13. dashboard.py lee el JSON y actualiza la interfaz
```

---

## 🚀 Instalación y Ejecución

### Requisitos
- Docker y Docker Compose instalados
- Arduino conectado por USB con el sketch `riego.ino` cargado
- Sensor YL-69, relé y bomba conectados según el esquema del circuito

---

### Pasos

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/eze-c/Riego-.git
   cd Riego-
   ```

2. **Crear el archivo de configuración**
   ```bash
   cp .env.example .env
   # Editá .env con el puerto USB correcto
   ```

3. **Verificar el puerto del Arduino**
   ```bash
   ls /dev/tty*
   # Buscá /dev/ttyUSB0, /dev/ttyUSB1 o /dev/ttyACM0
   ```

4. **Construir e iniciar**
   ```bash
   docker-compose up --build
   ```

5. **Acceder al dashboard**
   ```
   http://localhost:8501
   ```

6. **Ver los logs en tiempo real**
   ```bash
   docker logs riego--app-1 -f
   ```

---

## ⚙️ Configuración

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `ARDUINO_PORT` | Puerto USB del Arduino | `/dev/ttyUSB1` |
| `HUMIDITY_THRESHOLD` | Humedad mínima para activar el riego (%) | `30` |
| `SERIAL_BAUD` | Velocidad de comunicación serial | `9600` |
| `DATA_FILE` | Ruta del archivo de datos compartido | `/app/datos_riego.json` |

---

## 🛠️ Problemas comunes

**`No such file or directory: /dev/ttyUSB0`**
- Verificá con `ls /dev/tty*` qué puerto tiene el Arduino
- Actualizá `ARDUINO_PORT` en el `.env` y reiniciá: `docker-compose restart`

**`Device or resource busy`**
- El Arduino IDE o el Monitor Serial está abierto y ocupando el puerto
- Cerrá esa aplicación y reiniciá Docker

**El dashboard muestra ERROR**
- `main.py` no pudo conectar con el Arduino
- Revisá los logs: `docker logs riego--app-1`
- Verificá que el Arduino tenga el sketch cargado y esté enchufado

---

## 📚 Tecnologías usadas

| Tecnología | Uso |
|-----------|-----|
| Arduino Uno | Microcontrolador y control del hardware |
| Python 3.9 | Lógica de control y comunicación serial |
| Streamlit | Dashboard web |
| Docker | Contenedor y portabilidad |
| PySerial | Comunicación serial con Arduino |
| Plotly | Gráficos interactivos |
| python-dotenv | Variables de entorno desde `.env` |

---

## 👤 Autor

Ezequiel Costilla
