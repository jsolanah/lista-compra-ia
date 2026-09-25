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
GEMINI_API_KEY = _obtener_configuracion("GEMINI_API_KEY", "")
GEMINI_MODEL = _obtener_configuracion("GEMINI_MODEL", "gemini-3.6-flash")
SUPABASE_URL = _obtener_configuracion("SUPABASE_URL", "")
SUPABASE_PUBLISHABLE_KEY = _obtener_configuracion("SUPABASE_PUBLISHABLE_KEY", "")
SUPABASE_SECRET_KEY = _obtener_configuracion("SUPABASE_SECRET_KEY", "")
SUPABASE_KEY = SUPABASE_SECRET_KEY or _obtener_configuracion("SUPABASE_KEY", "")
if GEMINI_MODEL in {
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-2.5-flash",
}:
    GEMINI_MODEL = "gemini-3.6-flash"

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
