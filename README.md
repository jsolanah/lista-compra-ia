# 🛒 Lista de la Compra Inteligente

Aplicación en Streamlit que analiza un PDF de dieta con Gemini y genera una
lista de la compra clasificada por categorías, con cantidades consolidadas
y checkboxes para marcar lo comprado.

## Estructura del proyecto

```
Dieta/
├── app.py                  # Punto de entrada de Streamlit (interfaz)
├── src/
│   ├── config.py           # Carga de .env, API key, modelo y categorías
│   ├── ai/
│   │   └── gemini_client.py # Prompt y llamada a la API de Gemini
│   ├── documents/
│   │   └── pdf_utils.py     # Extracción de texto del PDF
│   ├── exports/
│   │   └── export_utils.py  # Exportación de la lista a .txt
│   ├── jobs/
│   │   └── job_manager.py   # Trabajos de generación en segundo plano
│   └── persistence/
│       └── list_cache.py    # Caché SQLite de listas generadas
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
   ```

   Este archivo se lee en el servidor y **no se muestra ni es editable desde
   la interfaz**, para que la app pueda desplegarse públicamente sin exponer
   la clave ni el modelo a los usuarios.

## Ejecución

```
streamlit run app.py
```

Se abrirá en `http://localhost:8501`.

## Base de datos y caché

La aplicación usa SQLite para guardar las listas generadas en:

```text
data/listas_compra.db
```

Cada registro contiene:

- El nombre normalizado del PDF.
- La lista de la compra generada en formato JSON.
- La fecha de generación.

Antes de llamar a Gemini, la aplicación consulta esta base de datos. Si ya
existe una lista para ese nombre de PDF, la recupera directamente y no vuelve
a consumir tokens. Los nombres se normalizan para ignorar diferencias de
mayúsculas, espacios exteriores y Unicode entre dispositivos.

La base de datos se crea automáticamente al guardar la primera lista. Su ruta
se puede cambiar con la variable de entorno `LISTA_DB_PATH`:

```text
LISTA_DB_PATH=/ruta/persistente/listas_compra.db
```

En un despliegue público, la base debe estar en un almacenamiento persistente.
Si la plataforma reinicia la aplicación y usa un disco efímero, las listas
guardadas se perderán. La base local está excluida de Git mediante `.gitignore`
y no contiene la API key.

## Uso

1. Sube tu PDF de dieta desde la barra lateral.
2. Pulsa **Generar lista de la compra**.
3. Revisa la lista clasificada por categorías (🥩 Carne, 🐟 Pescado, 🥦 Verduras...).
4. Marca los checkboxes de lo que ya tengas o vayas comprando.
5. Descarga la lista final con el botón de exportar a `.txt`.

## Despliegue público

Al subir esta app a un servicio como Streamlit Community Cloud, configura
`GEMINI_API_KEY` y `GEMINI_MODEL` como **secrets** de la plataforma en lugar
de subir el archivo `.env` (que ya está excluido en `.gitignore`).
