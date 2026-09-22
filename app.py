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
# ---------------------------------------------

with st.sidebar:
    st.header("🛒 Lista de la Compra")
   + mdurl==0.1.2[2026-09-22 11:33:41.956311]

   + pygments==2.21.0

   + rich==15.0.0

─────────────────────────────────────────────────────────────────────────


  [11:33:42] 🐍 Python dependencies were installed from /mount/src/lista-compra-ia/requirements.txt using uv.

  Check if streamlit is installed

  Streamlit is already installed

  [11:33:43] 📦 Processed dependencies!

  2026-09-22 11:33:45.448 Uvicorn server started on :::8501




  /mount/src/lista-compra-ia/src/gemini_client.py:5: FutureWarning:


  All support for the `google.generativeai` package has ended. It will no longer be receiving

  updates or bug fixes. Please switch to the `google.genai` package as soon as possible.

  See README for more details:


  https://github.com/google-gemini/deprecated-generative-ai-python/blob/main/README.md


    import google.generativeai as genai

  2026-09-22 12:38:45.329 Session with id 4569a7b6-8282-4f92-b5a8-065c0aca28ae is already connected! Reconnecting to existing
  session.

  2026-09-22 12:38:57.885 Session with id 4569a7b6-8282-4f92-b5a8-065c0aca28ae is already connected! Reconnecting to existing session.

  [15:21:48] 🐙 Pulling code changes from Github...

  [15:21:49] 📦 Processing dependencies...

  [15:21:49] 📦 Processed dependencies!

  [15:21:50] 🔄 Updated app!

El log no muestra el traceback real porque el except Exception: en app.py:68 atrapa el error sin registrarlo en ningún sitio — solo veremos el warning de que google.generativeai está deprecado (que no es la causa, es solo un aviso). Para saber qué falla de verdad, voy a añadir una línea que imprima el error en los logs del servidor (sin mostrarlo al usuario), así la próxima vez que falle veremos la causa real.

● Update(app.py)
Added 2 lines, removed 1 line



  Ran 1 shell command

Esta carpeta local no está inicializada como repo git, pero el log muestra que Streamlit Cloud despliega desde un repo de GitHub llamado lista-compra-ia. Necesito saber cómo subes tú los cambios normalmente.

● User answered Claude's questions:
· ¿Cómo sincronizas normalmente esta carpeta local con el repo de GitHub 'lista-compra-ia' que usa Streamlit Cloud? → Solo he subido una vez los archivos a github manualmente, cuando he creado la app, no he vuelto a subir nada

Entendido, entonces para que este cambio (el que añade el log del error) llegue a Streamlit Cloud, tienes que volver a subir el archivo app.py manualmente a GitHub.

Pasos:

1. Ve al repositorio lista-compra-ia en github.com (tu cuenta).
2. Abre el archivo app.py en el repo, pulsa el icono de lápiz (✏️ Edit).
3. Borra su contenido y pega el nuevo (te lo dejo abajo), o dime si prefieres que te genere el archivo completo para copiar/pegar.
4. Haz commit directamente en main (botón "Commit changes").
5. Streamlit Cloud detectará el push y redepliegará solo (verás "🔄 Updated app!" en los logs, como en el pull de las 15:21 que ya viste).
6. Reproduce el error (súbele el PDF y genera la lista) desde el móvil que falla.
7. Vuelve a "Manage app" → Logs y busca la línea [ERROR generar_lista_compra] ... — cópiame esa línea completa.

¿Quieres que te pegue aquí el contenido completo de app.py actualizado para que lo copies tal cual a GitHub?

✻ Baked for 31s · done 17:33

> dame el codigo para actualizarlo

  Read 1 file

Ya está actualizado localmente. Copia y pega espy en GitHub (reemplazando todo el archivo):

"""
Generador inteligente de lista de la compra a partir de un PDF de dieta.
Usa Gemini (google-generativeai) para extraer y consolidar ingredientes.
"""

import io
import json

import streamlit as st

from src.config import CATEGORIAS, GEMINI_API_KEY, GEMINI_MODEL
from src.export_utils import exportar_a_texto
from src.gemini_client import generar_lista_com
from src.pdf_utils import extraer_texto_pdf

st.set_page_config(page_title="Lista de la Compra Inteligente", page_icon="🛒", layout="centered")


# ---------------------------------------------
# Barra lateral (sin datos sensibles: solo carga de archivo)
# --------------------------------------------------------------------------

with st.sidebar:
    st.header("🛒 Lista de la Compra")
    st.caption("Sube el PDF de tu dieta para generar la lista.")
    archivo_pdf = st.file_uploader("Sube tu PDF de dieta", type=["pdf"])
    procesar = st.button("🚀 Generar lista de la compra", use_container_width=True, disabled=not archivo_pdf)

-------------------------------------------------------------
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

                st.session_state.lista_compra =
                st.session_state.checks = {}
                st.success("¡Lista de la compra generada correctamente!")

        except json.JSONDecodeError:
            st.error("No se ha podido interpretar la respuesta. Inténtalo de nuevo.")
        except Exception as e:  # noqa: BLE001 - no exponemos detalles internos en un entorno público
            print(f"[ERROR generar_lista_compra
            st.error("Ha ocurrido un error al generar la lista. Inténtalo de nuevo más tarde.")


# ---------------------------------------------
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
