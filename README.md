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
│   ├── pdf_utils.py         # Extracción de texto del PDF
│   ├── gemini_client.py     # Prompt y llamada a la API de Gemini
│   └── export_utils.py      # Exportación de la lista a .txt
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
