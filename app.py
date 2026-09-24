"""
Generador inteligente de lista de la compra a partir de un PDF de dieta.
Usa Gemini (google-generativeai) para extraer y consolidar ingredientes.
"""

import io
import json
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from uuid import uuid4

import streamlit as st

from src.config import CATEGORIAS, GEMINI_API_KEY, GEMINI_MODEL
from src.export_utils import exportar_a_texto
from src.gemini_client import generar_lista_compra
from src.pdf_utils import extraer_texto_pdf

st.set_page_config(page_title="Lista de la Compra Inteligente", page_icon="🛒", layout="centered")


_executor = ThreadPoolExecutor(max_workers=2)
_jobs: dict[str, Future] = {}
_jobs_lock = threading.Lock()


def _procesar_dieta(pdf_bytes: bytes, api_key: str, modelo: str) -> dict:
    texto_dieta = extraer_texto_pdf(io.BytesIO(pdf_bytes))
    if not texto_dieta.strip():
        raise ValueError("No se ha podido extraer texto del PDF. ¿Es un PDF escaneado como imagen?")
    return generar_lista_compra(texto_dieta, api_key, modelo)


def _iniciar_procesamiento(pdf_bytes: bytes) -> str:
    job_id = uuid4().hex
    future = _executor.submit(_procesar_dieta, pdf_bytes, GEMINI_API_KEY, GEMINI_MODEL)
    with _jobs_lock:
        _jobs[job_id] = future
    return job_id


def _obtener_trabajo(job_id: str) -> Future | None:
    with _jobs_lock:
        return _jobs.get(job_id)


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
        st.session_state.generation_job_id = _iniciar_procesamiento(archivo_pdf.getvalue())
        st.session_state.lista_compra = None
        st.session_state.checks = {}


if "generation_job_id" not in st.session_state:
    st.session_state.generation_job_id = None


generation_job_id = st.session_state.generation_job_id
if generation_job_id:

    @st.fragment(run_every="2s")
    def mostrar_estado_generacion():
        future = _obtener_trabajo(generation_job_id)
        if future is None:
            st.error("Se ha perdido el proceso de generación. Vuelve a intentarlo.")
            return
        if not future.done():
            st.info("⏳ Generando la lista... Puedes bloquear el teléfono; el proceso continúa en el servidor.")
            return

        try:
            st.session_state.lista_compra = future.result()
            st.session_state.checks = {}
            st.session_state.generation_job_id = None
            st.rerun()
        except json.JSONDecodeError:
            st.session_state.generation_job_id = None
            st.error("No se ha podido interpretar la respuesta. Inténtalo de nuevo.")
        except Exception as e:
            st.session_state.generation_job_id = None
            st.error(f"⚠️ Error detallado: {e}")

    mostrar_estado_generacion()


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
        on_click="ignore",
        use_container_width=True,
    )
else:
    st.info("Sube un PDF y pulsa **Generar lista de la compra** en el panel lateral para empezar.")
