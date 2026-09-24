"""Persistencia local de listas generadas, indexadas por nombre de PDF."""

import json
import os
import sqlite3
from pathlib import Path


DB_PATH = Path(os.getenv("LISTA_DB_PATH", "data/listas_compra.db"))


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


def obtener_lista(nombre_pdf: str) -> dict | None:
    with _connect() as connection:
        fila = connection.execute(
            "SELECT datos_json FROM listas_compra WHERE nombre_pdf = ?",
            (nombre_pdf,),
        ).fetchone()
    return json.loads(fila[0]) if fila else None


def guardar_lista(nombre_pdf: str, datos: dict) -> None:
    datos_json = json.dumps(datos, ensure_ascii=False)
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO listas_compra (nombre_pdf, datos_json)
            VALUES (?, ?)
            ON CONFLICT(nombre_pdf) DO UPDATE SET
                datos_json = excluded.datos_json,
                creada_en = CURRENT_TIMESTAMP
            """,
            (nombre_pdf, datos_json),
        )
