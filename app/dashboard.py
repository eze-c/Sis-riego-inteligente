import streamlit as st
import plotly.express as px
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from utils import formatear_porcentaje

load_dotenv()

ARCHIVO_DATOS = os.getenv('DATA_FILE', '/app/datos_riego.json')
UMBRAL = int(os.getenv('HUMIDITY_THRESHOLD', 30))

def cargar_datos():
    """
    Lee el archivo JSON generado por main.py con los datos actuales del sistema.

    Returns:
        dict: diccionario con humedad_actual, estado e historial.
    """
    try:
        with open(ARCHIVO_DATOS, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'humedad_actual': None, 'estado': 'SIN DATOS', 'historial': []}

st.set_page_config(
    page_title="Sistema de Riego Inteligente",
    page_icon="💧",
    layout="centered"
)

st.title("💧 Sistema de Riego Inteligente")
st.caption(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")

datos = cargar_datos()

col1, col2 = st.columns(2)

with col1:
    humedad = datos.get('humedad_actual')
    st.metric("Humedad Actual", formatear_porcentaje(humedad))

with col2:
    estado = datos.get('estado', 'DESCONOCIDO')
    if estado == "REGANDO":
        st.warning(f"Estado: {estado} 🚿")
    elif estado == "OK":
        st.success(f"Estado: {estado} ✅")
    else:
        st.error(f"Estado: {estado} ❌")

st.markdown("---")

historial = datos.get('historial', [])
if historial:
    fig = px.line(
        x=list(range(len(historial))),
        y=historial,
        title="Historial de Humedad (%)",
        labels={'x': 'Lecturas', 'y': 'Humedad (%)'}
    )
    fig.add_hline(
        y=UMBRAL,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Umbral de riego ({UMBRAL}%)"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No hay datos históricos aún. Esperando lecturas del sensor...")

st.markdown("---")
st.write("**Configuración actual:**")
st.write(f"- Umbral de riego: {UMBRAL}%")
st.write("- El sistema riega automáticamente cuando la humedad baja del umbral")

if st.button("🔄 Actualizar"):
    st.rerun()