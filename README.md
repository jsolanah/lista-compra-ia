# 🛒 Lista de la Compra Inteligente

Aplicación en Streamlit que analiza un PDF de dieta con Gemini y genera una
lista de la compra clasificada por categorías, con cantidades consolidadas,
el plan de comidas semanal y checkboxes para marcar lo comprado.

## Estructura del proyecto

```
Dieta/
├── app.py                  # Punto de entrada de Streamlit (interfaz)
├── src/
│   ├── config.py           # Carga de .env, API key, modelo y categorías
│   ├── auth/
│   │   └── auth_manager.py  # Registro e inicio de sesión con Supabase Auth
│   ├── ai/
│   │   └── gemini_client.py # Prompt y llamada a la API de Gemini
│   ├── documents/
│   │   └── pdf_utils.py     # Extracción de texto del PDF
│   ├── exports/
│   │   └── export_utils.py  # Exportación de la lista a .txt
│   ├── jobs/
│   │   └── job_manager.py   # Trabajos de generación en segundo plano
│   └── persistence/
│       └── list_cache.py    # Persistencia Supabase (SQLite en local)
├── .streamlit/
│   └── config.toml         # Oculta el menú/toolbar de desarrollador
├── requirements.txt
└── .env                     # API key (no se sube a git, ver .gitignore)
```

## Instalación

1. Instala las dependencias:

   ```
   pip install -r requirements.txt
   ```

2. La clave de API de Gemini se configura en el archivo `.env`:

   ```
   GEMINI_API_KEY=tu_clave_aqui
   GEMINI_MODEL=gemini-3.6-flash
   SUPABASE_URL=https://tu-proyecto.supabase.co
   SUPABASE_PUBLISHABLE_KEY=tu-clave-publicable
   SUPABASE_SECRET_KEY=tu-clave-secreta
   ```

   Este archivo se lee en el servidor y **no se muestra ni es editable desde
   la interfaz**, para que la app pueda desplegarse públicamente sin exponer
   la clave ni el modelo a los usuarios.

## Ejecución

### Despliegue local en Windows

Desde PowerShell, situado en la carpeta raíz del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Crea un archivo `.env` en esa misma carpeta con la configuración de Gemini:

```env
GEMINI_API_KEY=tu_clave_de_gemini
GEMINI_MODEL=gemini-3.6-flash
```

Inicia la aplicación con Streamlit:

```powershell
streamlit run app.py
```

La aplicación estará disponible en `http://localhost:8501`. Debe iniciarse
con `streamlit run app.py`, no con `python app.py`.

Si no se configuran las credenciales de Supabase, la base de datos local se
crea automáticamente en `data/listas_compra.db`.

### Ejecución rápida

```
streamlit run app.py
```

Se abrirá en `http://localhost:8501`.

## Base de datos y caché

En producción, la aplicación usa Supabase para guardar las listas generadas.
En desarrollo, si no hay credenciales de Supabase, utiliza SQLite en:

```text
data/listas_compra.db
```

Cada registro contiene:

- El nombre normalizado del PDF.
- La lista de la compra y el plan de comidas semanal generados en formato JSON.
- La fecha de generación.

En el editor SQL de Supabase, si todavía no tienes la tabla, crea el esquema
de usuarios y dietas:

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

Si ya tienes la tabla nueva con `usuario_id` pero sin `nombre_archivo`, añade la
columna:

```sql
alter table public.listas_compra
add column if not exists nombre_archivo text;
```

Si ya habías creado la tabla anterior sin `usuario_id`, renómbrala antes de
ejecutar el bloque anterior para conservarla como respaldo:

```sql
alter table public.listas_compra rename to listas_compra_legacy;
```

Antes de llamar a Gemini, la aplicación consulta esta base de datos. Si ya
existe una lista para ese PDF, aunque la haya generado otra cuenta, la
recupera directamente y no vuelve a consumir tokens. La clave del PDF se
calcula con SHA-256 a partir de su contenido.

Para usar Supabase localmente, añade `SUPABASE_URL` y `SUPABASE_SECRET_KEY` al
archivo `.env`. En Streamlit Cloud, configúralas en `Settings > Secrets`:

```toml
SUPABASE_URL = "https://tu-proyecto.supabase.co"
SUPABASE_PUBLISHABLE_KEY = "tu-clave-publicable"
SUPABASE_SECRET_KEY = "tu-clave-secreta"
```

La clave publicable se usa para Supabase Auth. La clave secreta se usa solo en
el servidor para guardar datos y nunca debe exponerse ni subirse a GitHub.

La aplicación exige iniciar sesión antes de permitir subir o consultar dietas.
En **Mis dietas** cada usuario puede abrir sus listas guardadas sin volver a
subir el PDF. Si otro usuario sube el mismo PDF, se reutiliza la respuesta de
Gemini y se crea su propia entrada en el historial.
Configura en Supabase si los usuarios deben confirmar su correo electrónico
desde `Authentication > Providers > Email`.

La base de datos se crea automáticamente al guardar la primera lista. Su ruta
se puede cambiar con la variable de entorno `LISTA_DB_PATH`:

```text
LISTA_DB_PATH=/ruta/persistente/listas_compra.db
```

Al activar Supabase, los datos dejan de depender del disco efímero del servidor
de Streamlit. La base local está excluida de Git mediante `.gitignore` y no
contiene la API key.

## Uso

1. Selecciona **Nueva dieta** en la pantalla principal.
2. Sube tu PDF y pulsa **Generar lista de la compra**.
3. Revisa las tablas del plan de comidas de cada semana.
4. Revisa la lista clasificada por categorías (🥩 Carne, 🐟 Pescado, 🥦 Verduras...).
5. Marca los checkboxes de lo que ya tengas o vayas comprando.
6. Descarga la lista final con el botón de exportar a `.txt`.

## Despliegue público

Al subir esta app a un servicio como Streamlit Community Cloud, configura
`GEMINI_API_KEY`, `GEMINI_MODEL`, `SUPABASE_URL`,
`SUPABASE_PUBLISHABLE_KEY` y `SUPABASE_SECRET_KEY` como **secrets** de la
plataforma en lugar de subir el archivo `.env` (que ya está excluido en
`.gitignore`).
