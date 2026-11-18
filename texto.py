"""Preprocesamiento de texto que comparten el entrenamiento y el bot.

Es MUY importante que el modelo procese el texto igual cuando entrena y cuando
predice; por eso esta lógica vive en un solo archivo.
"""
import json
import re
import unicodedata
from pathlib import Path

DATOS = json.loads((Path(__file__).parent / "datos" / "liga.json").read_text(encoding="utf-8"))


def normalizar(texto: str) -> str:
    """Minúsculas, sin tildes y sin signos: '¿Cuántas estrellas tiene Millos?' -> 'cuantas estrellas tiene millos'."""
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")  # quita las tildes
    texto = re.sub(r"[^a-z0-9ñ ]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


# Lista (alias, id_equipo) ordenada del alias más largo al más corto,
# para que "deportivo cali" se detecte antes que "cali".
_ALIAS = sorted(
    ((normalizar(a), clave) for clave, eq in DATOS["equipos"].items() for a in eq["alias"]),
    key=lambda par: len(par[0]),
    reverse=True,
)


def buscar_equipo(texto: str) -> str | None:
    """Devuelve el id del equipo mencionado en el texto (ej. 'millonarios'), o None."""
    t = f" {normalizar(texto)} "
    for alias, clave in _ALIAS:
        if f" {alias} " in t:
            return clave
    return None


def preparar(texto: str) -> str:
    """Normaliza y reemplaza el nombre del equipo por la palabra 'equipox'.

    Así el modelo aprende la FORMA de la pregunta ("cuántas estrellas tiene ___")
    y no se confunde por el nombre del equipo.
    """
    t = f" {normalizar(texto)} "
    for alias, _ in _ALIAS:
        t = t.replace(f" {alias} ", " equipox ")
    return t.strip()
