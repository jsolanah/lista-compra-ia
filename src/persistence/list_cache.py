"""Persistencia local de listas generadas, indexadas por nombre de PDF."""

import json
import os
import sqlite3
import unicodedata
from contextlib import closing
from pathlib import Path

from src.config import SUPABASE_KEY, SUPABASE_URL


DB_PATH = Path(os.getenv("LISTA_DB_PATH", "data/listas_compra.db"))
_supabase_client = None


def normalizar_nombre_pdf(nombre_pdf: str) -> str:
    nombre = Path(nombre_pdf).name.strip()
    return unicodedata.normalize("NFC", nombre).casefold()


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS listas_compra (
            nombre_pdf TEXT PRIMARY KEY,
            datos_json TEXT NOT NULL,
            creada_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return connection


def _obtener_cliente_supabase():
    global _supabase_client
    if _supabase_client is None:
        try:
            from supabase import create_client
        except ImportError as error:
            raise RuntimeError(
                "Falta instalar la dependencia supabase. Ejecuta: pip install -r requirements.txt"
            ) from error
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client


def _usar_supabase() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


def _decodificar_datos(datos) -> dict:
    return json.loads(datos) if isinstance(datos, str) else datos


def obtener_lista(nombre_pdf: str) -> dict | None:
    nombre_normalizado = normalizar_nombre_pdf(nombre_pdf)
    if _usar_supabase():
        respuesta = (
            _obtener_cliente_supabase()
            .table("listas_compra")
            .select("datos_json")
            .eq("nombre_pdf", nombre_normalizado)
            .limit(1)
            .execute()
        )
        filas = getattr(respuesta, "data", None) or []
        return _decodificar_datos(filas[0]["datos_json"]) if filas else None

    with closing(_connect()) as connection:
        fila = connection.execute(
            "SELECT datos_json FROM listas_compra WHERE nombre_pdf = ?",
            (nombre_normalizado,),
        ).fetchone()
        if fila is None:
            fila = connection.execute(
                """
                SELECT datos_json FROM listas_compra
                WHERE lower(trim(nombre_pdf)) = lower(trim(?))
                """,
                (nombre_pdf,),
            ).fetchone()
    return _decodificar_datos(fila[0]) if fila else None


def guardar_lista(nombre_pdf: str, datos: dict) -> None:
    nombre_normalizado = normalizar_nombre_pdf(nombre_pdf)
    if _usar_supabase():
        _obtener_cliente_supabase().table("listas_compra").upsert(
            {"nombre_pdf": nombre_normalizado, "datos_json": datos},
            on_conflict="nombre_pdf",
        ).execute()
        return

    datos_json = json.dumps(datos, ensure_ascii=False)
    with closing(_connect()) as connection:
        connection.execute(
            """
            INSERT INTO listas_compra (nombre_pdf, datos_json)
            VALUES (?, ?)
            ON CONFLICT(nombre_pdf) DO UPDATE SET
                datos_json = excluded.datos_json,
                creada_en = CURRENT_TIMESTAMP
            """,
            (nombre_normalizado, datos_json),
        )
        connection.commit()
