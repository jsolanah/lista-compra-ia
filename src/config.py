"""Configuración y constantes de la aplicación."""

import os

from dotenv import load_dotenv

load_dotenv()

# La API Key y el modelo se gestionan en el servidor: nunca se exponen en la UI
# pública para evitar que cualquier visitante consuma o cambie la configuración.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
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
