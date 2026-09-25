# 🛒 Lista de la compra inteligente

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white) ![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit&logoColor=white) ![Gemini](https://img.shields.io/badge/Gemini-AI-8A2BE2) ![Supabase](https://img.shields.io/badge/Supabase-Auth%20%2B%20DB-3ECF8E?logo=supabase&logoColor=white)

Aplicación web desarrollada con Streamlit para transformar un PDF de dieta en una lista de la compra estructurada y accionable. La app extrae el contenido del documento, interpreta los ingredientes, consolida cantidades y clasifica los productos por categoría para facilitar la compra.

## Menú

- [Descripción](#descripción)
- [Funcionalidades principales](#funcionalidades-principales)
- [Inicio rápido](#inicio-rápido)
- [Stack tecnológico](#stack-tecnológico)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Requisitos previos](#requisitos-previos)
- [Instalación](#instalación)
- [Ejecución local](#ejecución-local)
- [Funcionamiento](#funcionamiento)
- [Persistencia](#persistencia)
- [Supabase](#supabase)
- [Pruebas](#pruebas)
- [Consideraciones de despliegue](#consideraciones-de-despliegue)
- [Licencia](#licencia)

## Descripción

La solución permite:

- subir un PDF con un plan de alimentación o dieta.
- extraer el texto del documento.
- analizar el contenido con Gemini.
- consolidar ingredientes y cantidades.
- clasificar la compra en categorías estandarizadas.
- mostrar el plan semanal de comidas.
- guardar la información por usuario y reutilizar resultados si se vuelve a subir el mismo archivo.
- exportar la lista resultante a formato `.txt`.

## Funcionalidades principales

- Procesamiento automático de PDFs con extracción de texto.
- Generación inteligente de listas de la compra usando IA.
- Consolidación de cantidades por ingrediente.
- Categorización por tipo de producto.
- Visualización del plan semanal de comidas.
- Gestión de sesiones por usuario.
- Persistencia local y en Supabase.
- Exportación de la lista a texto plano.

## Inicio rápido

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

## Stack tecnológico

- Python 3.
- Streamlit.
- Google Gemini API.
- Supabase Auth y almacenamiento.
- SQLite como fallback local.
- PDF processing con `pdfplumber`.

## Estructura del proyecto

```text
lista-compra-ia/
├── app.py
├── requirements.txt
├── README.md
├── data/
├── src/
│   ├── ai/
│   │   └── gemini_client.py
│   ├── auth/
│   │   └── auth_manager.py
│   ├── documents/
│   │   └── pdf_utils.py
│   ├── exports/
│   │   └── export_utils.py
│   ├── jobs/
│   │   └── job_manager.py
│   ├── persistence/
│   │   └── list_cache.py
│   ├── config.py
│   └── __init__.py
├── tests/
│   └── test_list_cache.py
├── .env
└── .gitignore
```

## Requisitos previos

- Python 3.10+.
- Cuenta de Google AI / Gemini con API key.
- Cuenta de Supabase (opcional, para autenticación y persistencia en producción).
- Dependencias del proyecto instaladas.

## Instalación

1. Clona el repositorio y entra en la carpeta del proyecto.
2. Crea un entorno virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Instala las dependencias:

```powershell
python -m pip install -r requirements.txt
```

4. Crea un archivo `.env` en la raíz con las variables necesarias:

```env
GEMINI_API_KEY=tu_clave_de_gemini
GEMINI_MODEL=gemini-3.6-flash
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_PUBLISHABLE_KEY=tu_clave_publica
SUPABASE_SECRET_KEY=tu_clave_secreta
```

> Las variables de entorno se leen desde `.env`. En despliegue real, también pueden configurarse como secrets de la plataforma.

## Ejecución local

Desde la raíz del proyecto:

```powershell
streamlit run app.py
```

La aplicación se abre en:

```text
http://localhost:8501
```

## Funcionamiento

1. El usuario accede a la aplicación y se registra o inicia sesión.
2. Sube un PDF con la dieta o el plan alimenticio.
3. La app extrae el texto del documento.
4. Gemini interpreta los datos y devuelve un JSON con:
   - categorías de compra;
   - ingredientes consolidados;
   - cantidades;
   - plan semanal de comidas.
5. La app guarda los resultados por usuario y por hash del PDF.
6. El usuario puede revisar los productos, marcarlos como comprados y exportar la lista final.

## Persistencia

La app utiliza:

- Supabase cuando están configuradas las credenciales.
- SQLite local como fallback cuando no hay Supabase disponible.

Ruta por defecto de la base local:

```text
data/listas_compra.db
```

También puede definirse otra ruta con:

```text
LISTA_DB_PATH=/ruta/persistente/listas_compra.db
```

## Supabase

Si deseas usar Supabase en producción, crea la siguiente tabla:

```sql
create table public.listas_compra (
    usuario_id uuid not null references auth.users(id) on delete cascade,
    nombre_pdf text not null,
    nombre_archivo text,
    datos_json jsonb not null,
    creada_en timestamptz not null default now(),
    primary key (usuario_id, nombre_pdf)
);

alter table public.listas_compra enable row level security;
```

Si la tabla ya existe sin la columna `nombre_archivo`, puedes añadirla con:

```sql
alter table public.listas_compra
add column if not exists nombre_archivo text;
```

## Pruebas

Ejecuta la suite de pruebas con:

```powershell
python -m unittest discover -s tests -v
```

## Consideraciones de despliegue

En servicios públicos como Streamlit Community Cloud, no debes incluir secretos en el repositorio. Configúralos como variables de entorno o secrets de la plataforma.

Las variables que normalmente se requieren son:

- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY`
- `SUPABASE_SECRET_KEY`

## Licencia

Este proyecto se distribuye con fines de desarrollo y uso interno. Ajusta la licencia según el contexto del proyecto antes de desplegarlo públicamente.
