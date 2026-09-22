"""
Generador inteligente de lista de la compra a partir de un PDF de dieta.
Usa Gemini (google-generativeai) para extraer y consolidar ingredientes.
"""

import io
import json

import streamlit as st

from src.config import CATEGORIAS, GEMINI_API_KEY, GEMINI_MODEL
from src.export_utils import exportar_a_texto
from src.gemini_client import generar_lista_compra
from src.pdf_utils import extraer_texto_pdf

st.set_page_config(page_title="Lista de la Compra Inteligente", page_icon="🛒", layout="centered")


# --------------------------------------------------------------------------
# Barra lateral (sin datos sensibles: solo carga de archivo)
# --------------------------------------------------------------------------

with st.sidebar:
    st.header("🛒 Lista de la Compra")
    st.caption("Sube el PDF de tu dieta para generar la lista.")
    archivo_pdf = st.file_uploader("Sube tu PDF de dieta", type=["pdf"])
    procesar = st.button("🚀 Generar lista de la compra", use_container_width=True, disabled=not archivo_pdf)


# --------------------------------------------------------------------------
# Estado de sesión
# --------------------------------------------------------------------------

if "lista_compra" not in st.session_state:
    st.session_state.lista_compra = None
if "checks" not in st.session_state:
    st.session_state.checks = {}


# --------------------------------------------------------------------------
# Procesamiento
# --------------------------------------------------------------------------

st.title("🛒 Generador de Lista de la Compra")
st.caption("Sube el PDF de tu dieta y deja que la IA construya tu lista, clasificada y consolidada.")

if procesar and archivo_pdf:
    if not GEMINI_API_KEY:
        st.error("El servicio no está disponible en este momento. Inténtalo más tarde.")
    else:
        try:
            with st.spinner("📄 Extrayendo texto del PDF..."):
                texto_dieta = extraer_texto_pdf(io.BytesIO(archivo_pdf.getvalue()))

            if not texto_dieta.strip():
                st.error("No se ha podido extraer texto del PDF. ¿Es un PDF escaneado como imagen?")
            else:
                with st.spinner("🤖 Analizando la dieta..."):
                    datos = generar_lista_compra(texto_dieta, GEMINI_API_KEY, GEMINI_MODEL)

                st.session_state.lista_compra = datos
                st.session_state.checks = {}
                st.success("¡Lista de la compra generada correctamente!")

        except json.JSONDecodeError:
            st.error("No se ha podido interpretar la respuesta. Inténtalo de nuevo.")
        except Exception:  # noqa: BLE001 - no exponemos detalles internos en un entorno público
            st.error("Ha ocurrido un error al generar la lista. Inténtalo de nuevo más tarde.")


# --------------------------------------------------------------------------
# Resultado
# --------------------------------------------------------------------------

datos = st.session_state.lista_compra

if datos:
    st.divider()
    st.subheader("📋 Tu lista de la compra")

    categorias_presentes = {c["nombre"]: c for c in datos.get("categorias", [])}

    for nombre_categoria in CATEGORIAS:
        categoria = categorias_presentes.get(nombre_categoria)
        if not categoria or not categoria.get("items"):
            continue

        with st.expander(f"{nombre_categoria} ({len(categoria['items'])})", expanded=True):
            for item in categoria["items"]:
                clave = f"{nombre_categoria}|{item['ingrediente']}"
                marcado = st.checkbox(
                    f"{item['ingrediente']} — **{item['cantidad']}**",
                    key=clave,
                    value=st.session_state.checks.get(clave, False),
                )
                st.session_state.checks[clave] = marcado

    st.divider()
    texto_exportado = exportar_a_texto(datos, st.session_state.checks)
    st.download_button(
        "⬇️ Descargar lista (.txt)",
        data=texto_exportado,
        file_name="lista_de_la_compra.txt",
        mime="text/plain",
        use_container_width=True,
    )
else:
    st.info("Sube un PDF y pulsa **Generar lista de la compra** en el panel lateral para empezar.")
