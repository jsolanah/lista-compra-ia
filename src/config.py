"""Configuración y constantes de la aplicación."""

import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def _obtener_configuracion(nombre: str, valor_por_defecto: str) -> str:
    valor = os.getenv(nombre)
    if valor:
        return valor.strip().strip('"').strip("'")

    try:
        valor_secreto = st.secrets.get(nombre)
    except Exception:
        valor_secreto = None

    return str(valor_secreto).strip() if valor_secreto else valor_por_defecto


# La API key y el modelo se gestionan en el servidor: nunca se exponen en la
# interfaz pública.
OPENROUTER_API_KEY = _obtener_configuracion("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = _obtener_configuracion(
    "OPENROUTER_MODEL", "qwen/qwen3.8-27b:free"
)

CATEGORIAS = [
    "🥩 Carne",
    "🐟 Pescado",
    "🥚 Huevos y Lácteos",
    "🍞 Carbohidratos",
    "🥦 Verduras y Hortalizas",
    "🍎 Frutas",
    "🫒 Grasas, Aceites y Condimentos",
    "🛒 Otros / Varios",
]
