# ⚽ Bot de la Liga Colombiana (Telegram + Machine Learning)

Bot de Telegram que responde preguntas sobre la **Liga Profesional de Fútbol Colombiano (Liga BetPlay DIMAYOR)**: campeones, tabla de estrellas, equipos, estadios, clásicos, formato del torneo, descenso y una trivia con botones.

El usuario escribe como hablaría normalmente ("¿cuántas estrellas tiene millos?") y un **modelo de Machine Learning entrenado por nosotros** entiende qué quiere preguntar.

---

## 📁 Archivos del proyecto

| Archivo | Para qué sirve |
|---|---|
| `datos/frases_entrenamiento.csv` | Dataset: frases de ejemplo con su intención (lo que el usuario quiere) |
| `datos/liga.json` | Base de conocimiento: equipos, estrellas, campeones, clásicos, trivia |
| `texto.py` | Limpia el texto y detecta qué equipo se mencionó |
| `entrenar.py` | Entrena el modelo, lo evalúa y lo guarda en `modelo_intenciones.pkl` |
| `cerebro.py` | Usa el modelo para entender el mensaje y arma la respuesta |
| `bot.py` | Conecta todo con Telegram (comandos, mensajes y botones) |

---

## 🚀 Cómo ejecutarlo (Windows)

**1. Crear el bot en Telegram (desde el celular):** busca **@BotFather**, envía `/newbot`, elige un nombre y un usuario que termine en `bot`. Guarda el token que te da.

**2. Preparar el proyecto** (terminal en la carpeta del proyecto):

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**3. Configurar el token:** copia `.env.example`, renómbralo a `.env` y pega tu token:

```
TELEGRAM_TOKEN=123456789:ABC...
```

**4. Entrenar el modelo:**

```bash
python entrenar.py
```

**5. Encender el bot:**

```bash
python bot.py
```

Abre tu bot en Telegram, escribe `/start` y pregúntale lo que quieras. El bot responde mientras `bot.py` esté corriendo.

**Probar sin Telegram:** `python cerebro.py` abre un chat en la consola y muestra la intención detectada y la confianza.

---

## 💬 Qué se le puede preguntar

| Ejemplo | Intención que detecta |
|---|---|
| ¿Quién tiene más estrellas? | `campeones_historicos` |
| ¿Quién fue el último campeón? | `ultimo_campeon` |
| ¿Cuántas estrellas tiene el DIM? | `titulos_equipo` |
| ¿Dónde juega el leopardo? | `estadio_equipo` |
| Háblame del tiburón | `info_equipo` |
| ¿Cuál es el clásico paisa? | `clasicos` |
| ¿Cómo funcionan los cuadrangulares? | `formato` |
| ¿Quién baja a la B? | `descenso` |
| ¿Qué equipos hay? | `equipos_liga` |
| ¿Quién tiene más puntos en la liga? | `tabla_posiciones` (avisa que no tiene datos en vivo) |
| Quiero jugar trivia | `trivia` |

Comandos: `/start` `/ayuda` `/campeones` `/ultimos` `/equipos` `/equipo nacional` `/formato` `/descenso` `/clasicos` `/trivia`

---

## 🎓 Guía para la sustentación

### ¿Cómo funciona un bot de Telegram?
1. El bot se registra con **@BotFather**, que entrega un **token**: la clave que autoriza a nuestro programa a actuar como el bot. Va en `.env` y nunca se sube a GitHub.
2. El programa usa **polling**: le pregunta constantemente a Telegram si hay mensajes nuevos (`app.run_polling()`). Por eso el bot solo responde mientras `bot.py` está corriendo.
3. Cada tipo de mensaje tiene un **handler** (manejador): una función que decide qué hacer.
   - `CommandHandler`: comandos como `/campeones`.
   - `MessageHandler`: texto libre; aquí actúa el modelo de ML.
   - `CallbackQueryHandler`: clics en los botones de la trivia.

### ¿Dónde está el Machine Learning?
Es un problema de **clasificación de texto**: dado un mensaje, predecir su **intención** entre 15 categorías. Es aprendizaje **supervisado**, porque entrenamos con frases que ya tienen su respuesta correcta (la etiqueta).

1. **Dataset:** `frases_entrenamiento.csv`, con unas 250 frases etiquetadas en 15 intenciones.
2. **Preprocesamiento** (`texto.py`): minúsculas, quitar tildes y signos, y reemplazar el nombre del equipo por la palabra `equipox`. Así el modelo aprende la *forma* de la pregunta ("cuántas estrellas tiene ___") sin depender del equipo.
3. **Vectorización TF-IDF:** el modelo no entiende letras, solo números. TF-IDF convierte cada frase en números según qué palabras aparecen y qué tan importantes son (una palabra que aparece en todas las frases, como "el", pesa poco). Usamos palabras y también grupos de 2 a 4 letras, para tolerar errores de ortografía: "estreyas" se parece a "estrellas".
4. **Clasificador: Regresión Logística.** Aprende qué combinación de palabras corresponde a cada intención y da una **probabilidad** para cada una.
5. **Evaluación con validación cruzada:** el dataset se divide en 5 partes; se entrena con 4 y se prueba con la que el modelo nunca vio, rotando 5 veces. El resultado (~77%) mide qué tan bien funciona con frases nuevas.
6. **Umbral de confianza:** si el modelo está menos de 45% seguro, el bot responde "no te entendí" en vez de inventar.

### ¿Cómo encuentra el equipo?
Con **reglas** (no ML): `liga.json` tiene los nombres y apodos de cada equipo ("millos", "el tiburón", "DIM") y el bot busca si alguno aparece en el mensaje. El modelo dice *qué* se pregunta y las reglas dicen *de quién*. Combinar ML con reglas es un enfoque **híbrido**, igual que en el proyecto de ejemplo.

### Comparación con el proyecto de ejemplo
El ejemplo usa modelos **preentrenados** (pysentimiento) para detectar emociones. Este proyecto **entrena su propio modelo** con datos propios, lo que permite mostrar el ciclo completo de ML: dataset → preprocesamiento → entrenamiento → evaluación → predicción.

### ¿Qué pasa con una pregunta que el modelo no conoce?
El modelo solo puede elegir entre las intenciones con las que fue entrenado. Al principio no existía `tabla_posiciones`, y "¿quién tiene más puntos?" se confundía con "¿quién tiene más estrellas?". La solución fue **agregar ejemplos de la nueva intención al dataset y reentrenar**: así se mejora un modelo de ML, con más y mejores datos.

### Limitaciones y mejoras posibles
- El bot no tiene la tabla de posiciones ni resultados en vivo; los datos de la liga están en `liga.json`, así que hay que actualizarlos a mano después de cada final. Una mejora sería conectar una API de fútbol con resultados en vivo.
- Con más frases en el dataset, la precisión del modelo sube.
- Se podría guardar el puntaje de la trivia de cada usuario en una base de datos.

---

*Datos de la liga actualizados a noviembre de 2026 (campeón 2026-I: Junior).*
