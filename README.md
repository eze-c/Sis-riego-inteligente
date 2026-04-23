# 💧 Sistema de Riego Inteligente

Un sistema automatizado de riego que monitorea la humedad del suelo y activa una bomba de agua cuando es necesario.

## 🎯 Objetivo

Crear un sistema que lea datos de un sensor de humedad en tiempo real y controle automáticamente el riego basándose en umbrales configurables.

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────┐
│               Sensor de Humedad (Suelo)             │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│    Arduino (Lee sensor → Comunica por USB)          │
│  - Lectura analógica cada 2 segundos                │
│  - Protocolo: GET_HUMIDITY, WATER                   │
└──────────────────────┬──────────────────────────────┘
                       │ USB Serial
                       ▼
┌─────────────────────────────────────────────────────┐
│  Docker Container (Python + Streamlit)              │
│  ┌──────────────────────────────────────────────┐   │
│  │  main.py (Lógica de riego)                   │   │
│  │  - Lee datos del Arduino                     │   │
│  │  - Verifica umbral de humedad                │   │
│  │  - Activa relé si es necesario               │   │
│  │  - Genera datos_riego.json                   │   │
│  └──────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────┐   │
│  │  dashboard.py (Interfaz web)                 │   │
│  │  - Streamlit en puerto 8501                  │   │
│  │  - Visualiza humedad en tiempo real          │   │
│  │  - Historial de lecturas                     │   │
│  │  - Boton para actualizar datos               │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│    Relé → Bomba de Agua (Activación automática)     │
└─────────────────────────────────────────────────────┘
```

## 📁 Estructura del Proyecto

```
riego-inteligente/
├── arduino/
│   └── riego.ino              # Código del microcontrolador
├── app/
│   ├── main.py                # Lógica principal (lectura y control)
│   ├── dashboard.py           # Interfaz web con Streamlit
│   └── utils.py               # Funciones auxiliares (serial, formateo)
├── .env                       # Variables de entorno (no se sube a Git)
├── .env.example               # Plantilla de configuración
├── .gitignore                 # Archivos ignorados por Git
├── docker-compose.yml         # Orquestación de contenedores
├── Dockerfile                 # Imagen Docker para la aplicación
├── requirements.txt           # Dependencias Python
└── README.md                  # Este archivo
```

## 🚀 Instalación y Ejecución

### Requisitos
- Docker y Docker Compose instalados
- Arduino conectado a puerto USB (`/dev/ttyUSB0` en Linux)
- Sensor de humedad conectado al Arduino
- Relé y bomba de agua (conexión física al Arduino)

### Pasos

1. **Clonar el repositorio**
   ```bash
   git clone <tu-repo>
   cd riego-inteligente
   ```

2. **Crear archivo de configuración**
   ```bash
   cp .env.example .env
   # Edita .env según tu configuración (puerto USB, umbral de humedad, etc.)
   ```

3. **Construir e iniciar los contenedores**
   ```bash
   docker-compose up --build -d
   ```

4. **Acceder al dashboard**
   - Abre en tu navegador: `http://localhost:8501`

5. **Ver logs del sistema**
   ```bash
   docker logs riego--app-1 -f
   ```

## ⚙️ Configuración

Edita el archivo `.env` para ajustar:

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `ARDUINO_PORT` | Puerto USB del Arduino | `/dev/ttyUSB0` |
| `HUMIDITY_THRESHOLD` | Humedad mínima para activar riego (%) | `30` |
| `SERIAL_BAUD` | Velocidad de comunicación serial | `9600` |
| `DATA_FILE` | Ruta del archivo de datos compartido | `/app/datos_riego.json` |

## 💻 Descripción del Código

### 1. `arduino/riego.ino`
Código del microcontrolador que:
- Lee el sensor de humedad analógico (A0)
- Comunica con Python mediante serial
- Controla el relé que activa la bomba (pin digital 7)
- Responde a comandos: `GET_HUMIDITY` y `WATER`

### 2. `app/main.py`
Script principal que corre continuamente dentro del contenedor:
- Se conecta al Arduino por USB
- Lee humedad cada 2 segundos
- Compara con el umbral configurado
- Activa el riego si humedad < umbral
- Guarda histórico en `datos_riego.json`

### 3. `app/dashboard.py`
Interfaz web con Streamlit que:
- Carga datos de `datos_riego.json` en tiempo real
- Muestra métrica actual de humedad
- Gráfico interactivo del historial
- Botón para riego manual
- Información sobre el estado del sistema

### 4. `app/utils.py`
Funciones auxiliares para:
- Conexión serial con Arduino
- Envío/recepción de datos
- Validaciones y formateo

## 🔄 Flujo de Funcionamiento

1. **Arduino** lee sensor → envía humedad por USB
2. **main.py** recibe datos → decide si regar
3. Si humedad baja: **main.py** → Arduino → **Relé activa bomba**
4. **dashboard.py** lee `datos_riego.json` → muestra en web

## 🛠️ Troubleshooting

**Error: "Device or resource busy: /dev/ttyUSB0"**
- El puerto USB está en uso por otro proceso (ej: Arduino IDE, monitor serial)
- Solución: Cierra esa aplicación y reinicia Docker

**Dashboard muestra "SIN DATOS"**
- `main.py` no está corriendo o no logró conectar al Arduino
- Verifica logs: `docker logs riego--app-1`

**No hay conexión USB**
- Verifica el puerto: `ls /dev/tty*`
- Actualiza `.env` con el puerto correcto
- Reinicia: `docker-compose restart`

## 📚 Tecnologías

- **Arduino**: Microcontrolador y sensor
- **Python**: Lógica de negocio (3.9+)
- **Streamlit**: Dashboard web interactivo
- **Docker**: Containerización y portabilidad
- **PySerial**: Comunicación serial
- **Plotly**: Gráficos interactivos

