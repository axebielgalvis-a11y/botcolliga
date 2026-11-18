"""El "cerebro" del bot: entiende el mensaje y arma la respuesta.

No sabe nada de Telegram, así se puede probar solo (python cerebro.py).
Flujo:  mensaje -> modelo de ML (intención) + búsqueda de equipo -> respuesta
"""
import pickle
import random
from pathlib import Path

from texto import DATOS, buscar_equipo, preparar

# Si el modelo está menos seguro que esto, el bot dice que no entendió
UMBRAL_CONFIANZA = 0.45

INTENCIONES_DE_EQUIPO = {"info_equipo", "titulos_equipo", "estadio_equipo"}

with open(Path(__file__).parent / "modelo_intenciones.pkl", "rb") as f:
    MODELO = pickle.load(f)

EQUIPOS = DATOS["equipos"]


def nombre(clave: str) -> str:
    """Nombre bonito de un equipo, esté o no en la Primera A actual."""
    if clave in EQUIPOS:
        return EQUIPOS[clave]["nombre"]
    return DATOS["fuera_de_primera_a"].get(clave, clave)


def estrellas(clave: str) -> int:
    return DATOS["estrellas"].get(clave, 0)


# ─── Inteligencia artificial: predecir la intención ─────────────────────

def predecir_intencion(mensaje: str) -> tuple[str, float]:
    """Devuelve la intención más probable y qué tan seguro está el modelo (0 a 1)."""
    probabilidades = MODELO.predict_proba([preparar(mensaje)])[0]
    mejor = probabilidades.argmax()
    return MODELO.classes_[mejor], float(probabilidades[mejor])


# ─── Respuestas ─────────────────────────────────────────────────────────

def r_saludo(_):
    return random.choice([
        "¡Quiubo! ⚽ Soy el bot de la liga colombiana. Pregúntame por campeones, equipos, estadios, clásicos o el descenso.",
        "¡Hola, parce! ⚽ ¿Qué quieres saber de la Liga BetPlay? Escribe /ayuda para ver ejemplos.",
    ])


def r_despedida(_):
    return random.choice(["¡Chao! Que gane tu equipo. ⚽", "¡Nos vemos en el próximo partido! 👋"])


def r_agradecimiento(_):
    return random.choice(["¡Con gusto! ¿Algo más de la liga? ⚽", "¡De nada, parce! Pregunta lo que quieras."])


def r_ayuda(_):
    return (
        "⚽ <b>Puedes escribirme normal</b>, por ejemplo:\n"
        "• ¿Quién tiene más estrellas?\n"
        "• ¿Quién fue el último campeón?\n"
        "• ¿Cuántas estrellas tiene Millonarios?\n"
        "• ¿Dónde juega Junior?\n"
        "• Háblame del Medellín\n"
        "• ¿Cuál es el clásico paisa?\n"
        "• ¿Cómo funciona el descenso?\n"
        "• Quiero jugar trivia\n\n"
        "<b>Comandos:</b> /campeones /ultimos /equipos /formato /descenso /clasicos /trivia"
    )


def r_campeones_historicos(_):
    lineas = ["🏆 <b>Tabla de estrellas del fútbol colombiano</b> (solo títulos de liga)\n"]
    ranking = sorted(DATOS["estrellas"].items(), key=lambda par: -par[1])
    for pos, (clave, n) in enumerate(ranking, start=1):
        medalla = {1: "🥇", 2: "🥈", 3: "🥉"}.get(pos, f"{pos}.")
        lineas.append(f"{medalla} {nombre(clave)}: {n} ⭐")
    lineas.append(f"\n<i>Actualizado a {DATOS['actualizado']}.</i>")
    return "\n".join(lineas)


def r_ultimo_campeon(_):
    ultimo, *anteriores = DATOS["ultimos_campeones"]
    texto = (
        f"🏆 <b>Último campeón: {nombre(ultimo['campeon'])}</b> ({ultimo['torneo']})\n"
        f"Le ganó la final a {nombre(ultimo['subcampeon'])}; {ultimo['detalle']}.\n\n"
        "<b>Campeones anteriores:</b>\n"
    )
    for c in anteriores:
        texto += f"• {c['torneo']}: {nombre(c['campeon'])} (vs. {nombre(c['subcampeon'])})\n"
    return texto


def r_titulos_equipo(equipo):
    n = estrellas(equipo)
    if n == 0:
        return f"{nombre(equipo)} todavía no tiene estrellas de liga. ¡Algún día! 🙏"
    ranking = sorted(DATOS["estrellas"].values(), reverse=True)
    puesto = ranking.index(n) + 1
    texto = f"⭐ <b>{nombre(equipo)}</b> tiene <b>{n} {'estrella' if n == 1 else 'estrellas'}</b> de liga"
    texto += f" (puesto {puesto} en la tabla histórica)." if n > 1 else "."
    titulos_recientes = [c["torneo"] for c in DATOS["ultimos_campeones"] if c["campeon"] == equipo]
    if titulos_recientes:
        texto += f"\nTítulos recientes: {', '.join(titulos_recientes)}."
    return texto


def r_estadio_equipo(equipo):
    eq = EQUIPOS[equipo]
    return f"🏟️ <b>{eq['nombre']}</b> es de {eq['ciudad']} y su estadio es el <b>{eq['estadio']}</b>."


def r_info_equipo(equipo):
    eq = EQUIPOS[equipo]
    lineas = [f"⚽ <b>{eq['nombre']}</b>", f"📍 Ciudad: {eq['ciudad']}", f"🏟️ Estadio: {eq['estadio']}"]
    if eq.get("apodo"):
        lineas.append(f"🗣️ Apodo: {eq['apodo']}")
    if eq.get("colores"):
        lineas.append(f"🎨 Colores: {eq['colores']}")
    lineas.append(f"⭐ Estrellas de liga: {estrellas(equipo)}")
    for clasico in DATOS["clasicos"]:
        if equipo in clasico["equipos"]:
            rival = next(e for e in clasico["equipos"] if e != equipo)
            lineas.append(f"🔥 {clasico['nombre']} contra {nombre(rival)}")
    return "\n".join(lineas)


def r_clasicos(equipo):
    if equipo:
        propios = [c for c in DATOS["clasicos"] if equipo in c["equipos"]]
        if propios:
            return "\n".join(
                f"🔥 <b>{c['nombre']}</b>: {' vs. '.join(nombre(e) for e in c['equipos'])}"
                for c in propios
            )
    lineas = ["🔥 <b>Los clásicos del fútbol colombiano</b>\n"]
    for c in DATOS["clasicos"]:
        lineas.append(f"• <b>{c['nombre']}</b>: {' vs. '.join(nombre(e) for e in c['equipos'])} ({c['ciudad']})")
    return "\n".join(lineas)


def r_formato(_):
    return "📋 <b>¿Cómo funciona la liga?</b>\n\n" + "\n\n".join(f"• {p}" for p in DATOS["formato"])


def r_descenso(_):
    return "⬇️ <b>¿Cómo funciona el descenso?</b>\n\n" + "\n\n".join(f"• {p}" for p in DATOS["descenso"])


def r_equipos_liga(_):
    liga = DATOS["liga"]
    lineas = [f"⚽ <b>{liga['nombre_comercial']}</b>: {liga['numero_equipos']} equipos\n"]
    for eq in sorted(EQUIPOS.values(), key=lambda e: e["nombre"]):
        lineas.append(f"• {eq['nombre']} ({eq['ciudad']})")
    return "\n".join(lineas)


RESPUESTAS = {
    "saludo": r_saludo,
    "despedida": r_despedida,
    "agradecimiento": r_agradecimiento,
    "ayuda": r_ayuda,
    "campeones_historicos": r_campeones_historicos,
    "ultimo_campeon": r_ultimo_campeon,
    "titulos_equipo": r_titulos_equipo,
    "estadio_equipo": r_estadio_equipo,
    "info_equipo": r_info_equipo,
    "clasicos": r_clasicos,
    "formato": r_formato,
    "descenso": r_descenso,
    "equipos_liga": r_equipos_liga,
}

NO_ENTENDI = (
    "🤔 No te entendí bien. Pregúntame algo de la liga colombiana, por ejemplo:\n"
    "«¿Quién tiene más estrellas?» o «¿Dónde juega Millonarios?»\n"
    "Escribe /ayuda para ver más ejemplos."
)


def responder(mensaje: str) -> tuple[str, str, float]:
    """Devuelve (respuesta, intención, confianza). Si la intención es 'trivia',
    el bot de Telegram se encarga de enviar la pregunta con botones."""
    intencion, confianza = predecir_intencion(mensaje)
    equipo = buscar_equipo(mensaje)

    # Si el modelo está inseguro pero nombraron un equipo, mostramos su ficha
    if confianza < UMBRAL_CONFIANZA:
        if equipo in EQUIPOS:
            intencion = "info_equipo"
        else:
            return NO_ENTENDI, "desconocida", confianza

    if intencion == "trivia":
        return "", intencion, confianza

    if intencion in INTENCIONES_DE_EQUIPO:
        if equipo is None:
            return "¿De qué equipo? Escríbeme, por ejemplo: «¿Dónde juega Nacional?» ⚽", intencion, confianza

    return RESPUESTAS[intencion](equipo), intencion, confianza


if __name__ == "__main__":
    # Modo de prueba en la consola: escribe preguntas y mira qué responde el bot
    print("Prueba del cerebro del bot (escribe 'salir' para terminar)")
    while (mensaje := input("\nTú: ")).lower() != "salir":
        respuesta, intencion, confianza = responder(mensaje)
        print(f"[intención: {intencion} | confianza: {confianza:.0%}]")
        print(respuesta or "(aquí el bot enviaría una pregunta de trivia)")
