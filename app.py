"""
Generador inteligente de lista de la compra a partir de un PDF de dieta.
Usa Gemini (google-generativeai) para extraer y consolidar ingredientes.
"""

import io
import json
import threading
import base64
from concurrent.futures import Future, ThreadPoolExecutor
from uuid import uuid4

import streamlit as st

from src.config import CATEGORIAS, GEMINI_API_KEY, GEMINI_MODEL
from src.export_utils import exportar_a_texto
from src.gemini_client import generar_lista_compra
from src.pdf_utils import extraer_texto_pdf

st.set_page_config(page_title="Lista de la Compra Inteligente", page_icon="🛒", layout="centered")


@st.cache_resource
def _obtener_almacen_trabajos() -> tuple[ThreadPoolExecutor, dict[str, Future], threading.Lock]:
    return ThreadPoolExecutor(max_workers=2), {}, threading.Lock()


def _procesar_dieta(pdf_bytes: bytes, api_key: str, modelo: str) -> dict:
    texto_dieta = extraer_texto_pdf(io.BytesIO(pdf_bytes))
    if not texto_dieta.strip():
        raise ValueError("No se ha podido extraer texto del PDF. ¿Es un PDF escaneado como imagen?")
    return generar_lista_compra(texto_dieta, api_key, modelo)


def _iniciar_procesamiento(pdf_bytes: bytes) -> str:
    executor, jobs, jobs_lock = _obtener_almacen_trabajos()
    job_id = uuid4().hex
    future = executor.submit(_procesar_dieta, pdf_bytes, GEMINI_API_KEY, GEMINI_MODEL)
    with jobs_lock:
        jobs[job_id] = future
    return job_id


def _obtener_trabajo(job_id: str) -> Future | None:
    _, jobs, jobs_lock = _obtener_almacen_trabajos()
    with jobs_lock:
        return jobs.get(job_id)


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
    texto_codificado = base64.b64encode(texto_exportado.encode("utf-8")).decode("ascii")
    st.markdown(
        f"""
        <a href="data:text/plain;charset=utf-8;base64,{texto_codificado}"
           download="lista_de_la_compra.txt"
           target="_blank"
           rel="noopener noreferrer"
           style="display:block;width:100%;box-sizing:border-box;padding:0.6rem 1rem;
                  text-align:center;border:1px solid #ff4b4b;border-radius:0.5rem;
                  background:#ff4b4b;color:white;text-decoration:none;font-weight:600;">
            ⬇️ Descargar lista (.txt)
        </a>
        """,
        unsafe_allow_html=True,
    )
else:
    st.info("Sube un PDF y pulsa **Generar lista de la compra** en el panel lateral para empezar.")
