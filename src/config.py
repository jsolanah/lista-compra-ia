"""Configuración y constantes de la aplicación."""

import os

from dotenv import load_dotenv

load_dotenv()

# La API key y el modelo se gestionan en el servidor: nunca se exponen en la
# interfaz pública.
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")

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
