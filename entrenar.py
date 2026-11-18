"""Entrena el modelo que entiende qué quiere el usuario (su INTENCIÓN).

Uso:  python entrenar.py
Lee datos/frases_entrenamiento.csv, entrena, muestra qué tan bien funciona
y guarda el modelo en modelo_intenciones.pkl (el archivo que usa el bot).
"""
import csv
import pickle

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import FeatureUnion, Pipeline

from texto import preparar

# 1) Cargar el dataset: cada fila es una frase de ejemplo y su intención
with open("datos/frases_entrenamiento.csv", encoding="utf-8") as f:
    filas = list(csv.DictReader(f))
X = [preparar(fila["texto"]) for fila in filas]
y = [fila["intencion"] for fila in filas]
print(f"Dataset: {len(X)} frases, {len(set(y))} intenciones")


def crear_modelo() -> Pipeline:
    """2) El modelo tiene dos partes:
    - TF-IDF convierte el texto en números (qué palabras y pedazos de palabra aparecen
      y qué tan importantes son). Usamos palabras y también grupos de letras, para
      tolerar errores de ortografía ("cuantaz estreyas").
    - Regresión logística aprende, con esos números, a qué intención pertenece cada frase
      y da una probabilidad para cada intención.
    """
    vectorizador = FeatureUnion([
        ("palabras", TfidfVectorizer(ngram_range=(1, 2))),
        ("letras", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))),
    ])
    return Pipeline([
        ("tfidf", vectorizador),
        ("clasificador", LogisticRegression(max_iter=2000, C=10)),
    ])


# 3) Evaluación con validación cruzada: se divide el dataset en 5 partes; se entrena con 4
#    y se prueba con la que el modelo NO vio, rotando 5 veces. El promedio es la precisión.
puntajes = cross_val_score(crear_modelo(), X, y, cv=5)
print(f"Precisión (validación cruzada de 5 partes): {puntajes.mean():.0%}")
print("Precisión en cada parte:", ", ".join(f"{p:.0%}" for p in puntajes))

# 4) Modelo final: se entrena con TODAS las frases y se guarda
modelo_final = crear_modelo().fit(X, y)
with open("modelo_intenciones.pkl", "wb") as f:
    pickle.dump(modelo_final, f)
print("✅ Modelo guardado en modelo_intenciones.pkl")
