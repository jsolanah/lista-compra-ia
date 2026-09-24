"""Extracción y limpieza de texto de archivos PDF."""

import pdfplumber


def extraer_texto_pdf(archivo) -> str:
    """Extrae y limpia el texto de todas las páginas de un PDF."""
    texto_paginas = []
    with pdfplumber.open(archivo) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text() or ""
            texto_paginas.append(texto)

    texto_completo = "\n".join(texto_paginas)
    lineas = [linea.strip() for linea in texto_completo.splitlines()]
    lineas = [linea for linea in lineas if linea]
    return "\n".join(lineas)
