"""Comunicación con un modelo de Gemini a través de OpenRouter."""

import json

from openai import OpenAI

from src.config import CATEGORIAS


def construir_prompt(texto_dieta: str) -> str:
    categorias_lista = "\n".join(f"- {c}" for c in CATEGORIAS)
    return f"""Eres un asistente experto en nutrición y planificación de compras.
A continuación recibirás el texto completo extraído de un documento de dieta
(puede incluir varios días, comidas, cantidades en gramos, mililitros, unidades, etc.).

Tu tarea:
1. Identifica TODOS los ingredientes y alimentos necesarios para cumplir la dieta completa.
2. Si un mismo ingrediente aparece varias veces (en distintos días o comidas), SUMA y
   CONSOLIDA las cantidades en una sola entrada (ej: 200 g de pollo el lunes + 300 g el
   miércoles = 500 g de pollo). Normaliza unidades siempre que sea posible.
3. Clasifica cada ingrediente consolidado en UNA de estas categorías exactas:
{categorias_lista}
4. Ignora texto que no sean ingredientes (instrucciones, cabeceras, títulos, calorías, etc.).
5. Extrae también las tablas del plan de comidas. Conserva todas las semanas, días y
  comidas que aparezcan, respetando el texto y el orden del documento. No inventes
  comidas que no estén en el PDF.

Devuelve EXCLUSIVAMENTE un JSON válido (sin texto adicional, sin markdown, sin ```)
con esta estructura exacta:

{{
  "categorias": [
    {{
      "nombre": "🥩 Carne",
      "items": [
        {{"ingrediente": "Pechuga de pollo", "cantidad": "500 g"}}
      ]
    }}
  ],
  "plan_semanal": [
    {{
      "semana": "Semana 1",
      "dias": [
        {{
          "dia": "Lunes",
          "comidas": [
            {{"tipo": "Desayuno", "descripcion": "Avena con fruta"}},
            {{"tipo": "Comida", "descripcion": "Pollo con arroz"}}
          ]
        }}
      ]
    }}
  ]
}}

Incluye solo las categorías que tengan al menos un ingrediente. No inventes ingredientes
que no estén respaldados por el texto. Incluye solo semanas y días presentes en las
tablas; si no hay tablas de comidas, devuelve "plan_semanal": [].

TEXTO DE LA DIETA:
\"\"\"
{texto_dieta}
\"\"\"
"""


def parsear_respuesta_json(texto_respuesta: str) -> dict:
    """Extrae el bloque JSON de la respuesta del modelo, tolerando ```json ... ```"""
    texto = texto_respuesta.strip()
    if texto.startswith("```"):
        texto = texto.split("```")[1]
        if texto.startswith("json"):
            texto = texto[4:]
    texto = texto.strip("` \n")
    return json.loads(texto)


def generar_lista_compra(texto_dieta: str, api_key: str, modelo: str) -> dict:
    prompt = construir_prompt(texto_dieta)
    cliente = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "Lista de la Compra Inteligente",
        },
    )
    respuesta = cliente.chat.completions.create(
        model=modelo,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    contenido = respuesta.choices[0].message.content
    if not contenido:
        raise ValueError("OpenRouter ha devuelto una respuesta vacía.")
    return parsear_respuesta_json(contenido)
