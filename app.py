"""
Generador inteligente de lista de la compra a partir de un PDF de dieta.
Usa Gemini (google-generativeai) para extraer y consolidar ingredientes.
"""

import json
import base64

import streamlit as st
from streamlit_cookies_controller import CookieController

from src.auth.auth_manager import iniciar_sesion, registrar_usuario, restaurar_sesion
from src.config import CATEGORIAS, GEMINI_API_KEY, SUPABASE_PUBLISHABLE_KEY, SUPABASE_URL
from src.exports.export_utils import exportar_a_texto
from src.jobs.job_manager import iniciar_procesamiento, obtener_trabajo
from src.persistence.list_cache import (
    construir_clave_dieta,
    guardar_lista,
    obtener_dietas_usuario,
    obtener_lista,
)

st.set_page_config(page_title="Lista de la Compra Inteligente", page_icon="🛒", layout="centered")
cookies = CookieController(key="auth_cookies")


def _guardar_cookie_sesion(usuario: dict):
    try:
        secure = st.context.url.startswith("https://")
    except AttributeError:
        secure = True
    opciones = {"max_age": 60 * 60 * 24 * 30, "secure": secure, "same_site": "lax"}
    cookies.set("supabase_access_token", usuario["access_token"], **opciones)
    cookies.set("supabase_refresh_token", usuario["refresh_token"], **opciones)


def _borrar_cookie_sesion():
    cookies.remove("supabase_access_token")
    cookies.remove("supabase_refresh_token")


# --------------------------------------------------------------------------
# Autenticacion
# --------------------------------------------------------------------------

if "usuario" not in st.session_state:
    st.session_state.usuario = None

if st.session_state.usuario is None:
    access_token = cookies.get("supabase_access_token")
    refresh_token = cookies.get("supabase_refresh_token")
    if access_token and refresh_token:
        try:
            st.session_state.usuario = restaurar_sesion(access_token, refresh_token)
            _guardar_cookie_sesion(st.session_state.usuario)
        except Exception:
            _borrar_cookie_sesion()


def _limpiar_sesion_usuario():
    _borrar_cookie_sesion()
    st.session_state.usuario = None
    st.session_state.lista_compra = None
    st.session_state.checks = {}
    st.session_state.generation_job_id = None
    st.session_state.nombre_archivo_actual = ""


if st.session_state.usuario is None:
    st.title("🛒 Lista de la Compra Inteligente")
    st.caption("Inicia sesión para mantener tus dietas privadas.")

    if not SUPABASE_URL or not SUPABASE_PUBLISHABLE_KEY:
        st.error("Falta configurar la autenticación de Supabase.")
        st.stop()

    pestaña_login, pestaña_registro = st.tabs(["Iniciar sesión", "Crear cuenta"])
    with pestaña_login:
        with st.form("formulario_login"):
            email_login = st.text_input("Correo electrónico")
            password_login = st.text_input("Contraseña", type="password")
            enviar_login = st.form_submit_button("Iniciar sesión", use_container_width=True)
        if enviar_login:
            try:
                st.session_state.usuario = iniciar_sesion(email_login, password_login)
                _guardar_cookie_sesion(st.session_state.usuario)
                st.session_state.lista_compra = None
                st.session_state.checks = {}
                st.rerun()
            except Exception:
                st.error("No se ha podido iniciar sesión. Comprueba tus datos.")

    with pestaña_registro:
        with st.form("formulario_registro"):
            email_registro = st.text_input("Correo electrónico", key="registro_email")
            password_registro = st.text_input("Contraseña", type="password", key="registro_password")
            enviar_registro = st.form_submit_button("Crear cuenta", use_container_width=True)
        if enviar_registro:
            try:
                usuario_nuevo = registrar_usuario(email_registro, password_registro)
                if usuario_nuevo is None:
                    st.success("Cuenta creada. Revisa tu correo para confirmar la cuenta.")
                else:
                    st.session_state.usuario = usuario_nuevo
                    _guardar_cookie_sesion(st.session_state.usuario)
                    st.session_state.lista_compra = None
                    st.session_state.checks = {}
                    st.rerun()
            except Exception:
                st.error("No se ha podido crear la cuenta. Comprueba el correo y la contraseña.")
    st.stop()


# --------------------------------------------------------------------------
# Barra lateral (sin datos sensibles: solo carga de archivo)
# --------------------------------------------------------------------------

if "seccion" not in st.session_state:
    st.session_state.seccion = "Nueva dieta"
if "seccion_pendiente" in st.session_state:
    st.session_state.seccion = st.session_state.pop("seccion_pendiente")

with st.sidebar:
    st.header("🛒 Lista de la Compra")
    st.caption(f"Sesión: {st.session_state.usuario['email']}")
    if st.button("Cerrar sesión", use_container_width=True):
        _limpiar_sesion_usuario()
        st.rerun()
    st.divider()
    st.radio("Sección", ["Nueva dieta", "Mis dietas"], key="seccion")
    if st.session_state.seccion == "Nueva dieta":
        st.caption("Sube el PDF de tu dieta para generar la lista.")
        archivo_pdf = st.file_uploader("Sube tu PDF de dieta", type=["pdf"])
        procesar = st.button(
            "🚀 Generar lista de la compra",
            use_container_width=True,
            disabled=not archivo_pdf,
        )
    else:
        archivo_pdf = None
        procesar = False


# --------------------------------------------------------------------------
# Estado de sesión
# --------------------------------------------------------------------------

if "lista_compra" not in st.session_state:
    st.session_state.lista_compra = None
if "checks" not in st.session_state:
    st.session_state.checks = {}
if "nombre_archivo_actual" not in st.session_state:
    st.session_state.nombre_archivo_actual = ""


if st.session_state.seccion == "Mis dietas":
    st.title("📚 Mis dietas")
    st.caption("Abre una dieta guardada sin volver a subir el PDF.")
    dietas_guardadas = obtener_dietas_usuario(st.session_state.usuario["user_id"])

    if not dietas_guardadas:
        st.info("Todavía no tienes ninguna dieta guardada.")
    else:
        for indice, dieta in enumerate(dietas_guardadas):
            fecha = dieta["creada_en"][:10] if dieta["creada_en"] else ""
            etiqueta = dieta["nombre_archivo"]
            if fecha:
                etiqueta = f"{etiqueta} · {fecha}"
            with st.expander(etiqueta, expanded=False):
                st.caption(f"Hash del PDF: {dieta['nombre_pdf']}")
                if st.button("Abrir dieta", key=f"abrir_dieta_{indice}"):
                    st.session_state.lista_compra = dieta["datos"]
                    st.session_state.checks = {}
                    st.session_state.nombre_archivo_actual = dieta["nombre_archivo"]
                    st.session_state.seccion_pendiente = "Nueva dieta"
                    st.rerun()
    st.stop()


# --------------------------------------------------------------------------
# Procesamiento
# --------------------------------------------------------------------------

st.title("🛒 Generador de Lista de la Compra")
st.caption("Sube el PDF de tu dieta y deja que la IA construya tu lista, clasificada y consolidada.")

if procesar and archivo_pdf:
    pdf_bytes = archivo_pdf.getvalue()
    clave_dieta = construir_clave_dieta(pdf_bytes)
    usuario_id = st.session_state.usuario["user_id"]
    st.session_state.nombre_archivo_actual = archivo_pdf.name
    lista_guardada = obtener_lista(usuario_id, clave_dieta)
    if lista_guardada is not None and "plan_semanal" in lista_guardada:
        guardar_lista(usuario_id, clave_dieta, lista_guardada, archivo_pdf.name)
        st.session_state.lista_compra = lista_guardada
        st.session_state.checks = {}
        st.session_state.generation_job_id = None
        st.info("Dieta encontrada. Se han recuperado el plan y la lista guardados.")
    elif not GEMINI_API_KEY:
        st.error(
            "Falta configurar GEMINI_API_KEY en los Secrets de Streamlit Cloud."
        )
    else:
        st.session_state.generation_job_id = iniciar_procesamiento(pdf_bytes, clave_dieta)
        st.session_state.lista_compra = None
        st.session_state.checks = {}


if "generation_job_id" not in st.session_state:
    st.session_state.generation_job_id = None


generation_job_id = st.session_state.generation_job_id
if generation_job_id:

    @st.fragment(run_every="2s")
    def mostrar_estado_generacion():
        trabajo = obtener_trabajo(generation_job_id)
        if trabajo is None:
            st.error("Se ha perdido el proceso de generación. Vuelve a intentarlo.")
            return
        future, clave_dieta = trabajo
        if not future.done():
            st.markdown(
                """
                <style>
                    .loading-indicator {
                        display: flex;
                        align-items: center;
                        gap: 0.65rem;
                        padding: 0.75rem 1rem;
                        border-radius: 0.5rem;
                        background: rgba(49, 51, 63, 0.08);
                    }
                    .loading-spinner {
                        width: 1.1rem;
                        height: 1.1rem;
                        border: 0.18rem solid rgba(49, 51, 63, 0.2);
                        border-top-color: #ff4b4b;
                        border-radius: 50%;
                        animation: loading-spin 0.8s linear infinite;
                    }
                    @keyframes loading-spin {
                        to { transform: rotate(360deg); }
                    }
                </style>
                <div class="loading-indicator" role="status" aria-live="polite">
                    <span class="loading-spinner" aria-hidden="true"></span>
                    <span>Leyendo PDF, generando los datos...</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            return

        try:
            st.session_state.lista_compra = future.result()
            guardar_lista(
                st.session_state.usuario["user_id"],
                clave_dieta,
                st.session_state.lista_compra,
                st.session_state.nombre_archivo_actual,
            )
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
    plan_semanal = datos.get("plan_semanal", [])
    if plan_semanal:
        st.divider()
        st.subheader("🍽️ Plan de comidas")
        st.caption("Consulta las comidas previstas para cada día de tu dieta.")

        for semana in plan_semanal:
            nombre_semana = semana.get("semana", "Semana")
            filas = []
            for dia in semana.get("dias", []):
                comidas = dia.get("comidas", [])
                texto_comidas = "  \n".join(
                    f"**{comida.get('tipo', 'Comida')}**: {comida.get('descripcion', '')}"
                    for comida in comidas
                    if comida.get("descripcion")
                )
                if texto_comidas:
                    filas.append({"Día": dia.get("dia", ""), "Comidas": texto_comidas})

            if filas:
                with st.expander(nombre_semana, expanded=True):
                    st.table(filas)

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
