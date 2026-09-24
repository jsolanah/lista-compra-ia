"""Gestión de trabajos de generación en segundo plano."""

import io
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from uuid import uuid4

import streamlit as st

from src.ai.gemini_client import generar_lista_compra
from src.config import GEMINI_API_KEY, GEMINI_MODEL
from src.documents.pdf_utils import extraer_texto_pdf


@st.cache_resource
def _obtener_almacen_trabajos() -> tuple[ThreadPoolExecutor, dict[str, tuple[Future, str]], threading.Lock]:
    return ThreadPoolExecutor(max_workers=2), {}, threading.Lock()


def _procesar_dieta(pdf_bytes: bytes) -> dict:
    texto_dieta = extraer_texto_pdf(io.BytesIO(pdf_bytes))
    if not texto_dieta.strip():
        raise ValueError("No se ha podido extraer texto del PDF. ¿Es un PDF escaneado como imagen?")
    return generar_lista_compra(texto_dieta, GEMINI_API_KEY, GEMINI_MODEL)


def iniciar_procesamiento(pdf_bytes: bytes, nombre_pdf: str) -> str:
    executor, jobs, jobs_lock = _obtener_almacen_trabajos()
    with jobs_lock:
        for job_id, (future, nombre_en_proceso) in jobs.items():
            if nombre_en_proceso == nombre_pdf and not future.done():
                return job_id

        job_id = uuid4().hex
        jobs[job_id] = (executor.submit(_procesar_dieta, pdf_bytes), nombre_pdf)
    return job_id


def obtener_trabajo(job_id: str) -> tuple[Future, str] | None:
    _, jobs, jobs_lock = _obtener_almacen_trabajos()
    with jobs_lock:
        return jobs.get(job_id)
