"""Narrador de la partida: convierte el estado del juego en texto legible.

Capa de **presentación pura** (sin I/O, sin lógica de reglas). Dado el estado
ANTES y DESPUÉS de una acción, describe lo que pasó (cantos, quiero/no quiero
con su resultado, envido resuelto con los tantos, baza cerrada, fin de ronda).

Regla de dependencias: ``ui → game_loop → agents → core``. Este módulo solo lee
el estado del motor, nunca lo modifica.

El humano es el jugador 0 por defecto ("vos"); el rival es "la máquina".
"""

from __future__ import annotations

from truco.core.acciones import CANTOS_ENVIDO, CANTOS_TRUCO, Accion, TipoAccion
from truco.core.cards import Carta, Palo
from truco.core.state import EstadoObservable, EstadoRonda

# --- Cartas y jugadores ------------------------------------------------------

_SIMBOLO_PALO: dict[Palo, str] = {
    Palo.ESPADA: "♠",
    Palo.BASTO: "♣",
    Palo.ORO: "♦",
    Palo.COPA: "♥",
}

#: Valor del truco querido por nivel (para anunciar "se juega por N").
_VALOR_TRUCO = {1: 2, 2: 3, 3: 4}

_ANCHO = 48
_LINEA = "─" * _ANCHO


def carta_str(carta: Carta) -> str:
    """Nombre legible de una carta, con símbolo de palo. Ej: ``3 de espada ♠``."""
    return f"{carta.numero} de {carta.palo.value} {_SIMBOLO_PALO[carta.palo]}"


def _sujeto(jugador: int, humano: int) -> str:
    """Sujeto capitalizado para arrancar una frase: ``Vos`` / ``La máquina``."""
    return "Vos" if jugador == humano else "La máquina"


def _quien(jugador: int, humano: int) -> str:
    """Referencia en minúscula: ``vos`` / ``la máquina``."""
    return "vos" if jugador == humano else "la máquina"


def _se_lleva(jugador: int, humano: int, pts: int) -> str:
    """Frase conjugada bien: ``te llevás N`` / ``la máquina se lleva N``."""
    return f"te llevás {pts}" if jugador == humano else f"la máquina se lleva {pts}"


def _cadena_cantos(cantos: tuple[TipoAccion, ...]) -> str:
    return " → ".join(c.value for c in cantos)


# --- Narración de eventos (antes → acción → después) -------------------------


def narrar_evento(
    antes: EstadoRonda,
    quien: int,
    accion: Accion,
    despues: EstadoRonda,
    humano: int = 0,
) -> list[str]:
    """Describe en texto lo que produjo ``accion`` (una o más líneas)."""
    tipo = accion.tipo
    if tipo is TipoAccion.JUGAR:
        return _narrar_jugada(quien, accion, antes, despues, humano)
    if tipo in CANTOS_ENVIDO or tipo in CANTOS_TRUCO:
        return _narrar_canto(quien, accion, humano)
    if tipo is TipoAccion.QUIERO:
        return _narrar_quiero(quien, antes, despues, humano)
    if tipo is TipoAccion.NO_QUIERO:
        return _narrar_no_quiero(quien, antes, despues, humano)
    return _narrar_mazo(quien, antes, despues, humano)


def _narrar_jugada(
    quien: int, accion: Accion, antes: EstadoRonda, despues: EstadoRonda, humano: int
) -> list[str]:
    assert accion.carta is not None
    verbo = "tirás" if quien == humano else "tira"
    lineas = [f"  ▸ {_sujeto(quien, humano)} {verbo} el {carta_str(accion.carta)}"]
    if len(despues.bazas) > len(antes.bazas):  # se cerró una baza
        baza = despues.bazas[-1]
        if baza.ganador is None:
            lineas.append("     ═ la mano queda parda")
        else:
            lineas.append(f"     ═ la mano es para {_quien(baza.ganador, humano)}")
    return lineas


def _narrar_canto(quien: int, accion: Accion, humano: int) -> list[str]:
    verbo = "cantás" if quien == humano else "canta"
    return [f"  ▸ {_sujeto(quien, humano)} {verbo}: ¡{accion.tipo.value.upper()}!"]


def _narrar_quiero(quien: int, antes: EstadoRonda, despues: EstadoRonda, humano: int) -> list[str]:
    verbo = "querés" if quien == humano else "quiere"
    cabecera = f"  ▸ {_sujeto(quien, humano)} {verbo}"
    if despues.envido_resuelto and not antes.envido_resuelto:
        return [cabecera, *_resolucion_envido(antes, despues, humano, mostro_cartas=True)]
    if despues.truco_querido and not antes.truco_querido:
        valor = _VALOR_TRUCO.get(despues.nivel_truco, despues.nivel_truco + 1)
        return [cabecera, f"     ═ el truco se juega por {valor}"]
    return [cabecera]


def _narrar_no_quiero(
    quien: int, antes: EstadoRonda, despues: EstadoRonda, humano: int
) -> list[str]:
    verbo = "no querés" if quien == humano else "no quiere"
    cabecera = f"  ▸ {_sujeto(quien, humano)} {verbo}"
    if despues.envido_resuelto and not antes.envido_resuelto:
        return [cabecera, *_resolucion_envido(antes, despues, humano, mostro_cartas=False)]
    # No quiso el truco: se cierra la ronda y el que cantó se lleva los puntos.
    ganador = despues.ganador if despues.ganador is not None else quien
    pts = _delta(antes, despues, ganador)
    return [cabecera, f"     ═ {_se_lleva(ganador, humano, pts)} (no quisieron el truco)"]


def _resolucion_envido(
    antes: EstadoRonda, despues: EstadoRonda, humano: int, mostro_cartas: bool
) -> list[str]:
    cadena = _cadena_cantos(antes.pendiente.cantos) if antes.pendiente else "envido"
    ganador = despues.envido_ganador
    assert ganador is not None
    pts = despues.puntos_envido
    lineas = [f"     ═ envido ({cadena})"]
    if mostro_cartas:  # con "quiero" se muestran los tantos
        t_vos = despues.tantos[humano]
        t_maq = despues.tantos[1 - humano]
        lineas.append(f"     ═ tantos:  vos {t_vos}  —  {t_maq} la máquina")
        lineas.append(f"     ═ el envido es para {_quien(ganador, humano)}  (+{pts})")
    else:  # con "no quiero" nadie muestra las cartas
        verbo = "te llevás" if ganador == humano else "la máquina se lleva"
        lineas.append(f"     ═ {verbo} el envido (+{pts}), sin mostrar")
    return lineas


def _narrar_mazo(quien: int, antes: EstadoRonda, despues: EstadoRonda, humano: int) -> list[str]:
    verbo = "te vas" if quien == humano else "se va"
    ganador = despues.ganador if despues.ganador is not None else 1 - quien
    pts = _delta(antes, despues, ganador)
    return [
        f"  ▸ {_sujeto(quien, humano)} {verbo} al mazo",
        f"     ═ {_se_lleva(ganador, humano, pts)}",
    ]


def _delta(antes: EstadoRonda, despues: EstadoRonda, jugador: int) -> int:
    return despues.puntos_ronda[jugador] - antes.puntos_ronda[jugador]


# --- Tablero, menú y resúmenes ----------------------------------------------


def _mesa_str(obs: EstadoObservable) -> str:
    carta_mia = obs.mesa[obs.jugador]
    carta_rival = obs.mesa[1 - obs.jugador]
    partes = []
    if carta_mia is not None:
        partes.append(f"vos: {carta_str(carta_mia)}")
    if carta_rival is not None:
        partes.append(f"la máquina: {carta_str(carta_rival)}")
    return "  ·  ".join(partes) if partes else "— (nadie tiró todavía) —"


def tablero(obs: EstadoObservable, humano: int = 0) -> str:
    """El 'tablero' que ve el jugador antes de decidir su jugada."""
    yo = obs.puntos_partida[obs.jugador]
    otro = obs.puntos_partida[1 - obs.jugador]
    mias = sum(1 for b in obs.bazas if b.ganador == obs.jugador)
    rival = sum(1 for b in obs.bazas if b.ganador is not None and b.ganador != obs.jugador)
    rol = "sos mano" if obs.soy_mano else "mano la máquina"

    lineas = [
        _LINEA,
        f"  TRUCO · partida a {obs.objetivo}  ({rol})",
        _LINEA,
        f"  Marcador:  vos {yo}  —  {otro} la máquina",
        f"  Manos:     vos {mias}  —  {rival} la máquina",
        f"  En la mesa: {_mesa_str(obs)}",
    ]
    if obs.pendiente is not None:
        cadena = _cadena_cantos(obs.pendiente.cantos)
        lineas.append(f"  ⚠ Te cantaron: ¡{cadena.upper()}!  → tenés que responder")
    lineas.append("")
    lineas.append(f"  Tus cartas  (tu envido: {obs.mi_tanto}):")
    lineas.extend(f"     {carta_str(c)}" for c in obs.mi_mano)
    lineas.append(_LINEA)
    return "\n".join(lineas)


def _label_accion(accion: Accion) -> str:
    tipo = accion.tipo
    if tipo is TipoAccion.JUGAR:
        assert accion.carta is not None
        return f"jugar el {carta_str(accion.carta)}"
    if tipo is TipoAccion.QUIERO:
        return "QUIERO"
    if tipo is TipoAccion.NO_QUIERO:
        return "NO QUIERO"
    if tipo is TipoAccion.MAZO:
        return "irse al mazo"
    return f"cantar ¡{accion.tipo.value.upper()}!"


def menu(acciones: tuple[Accion, ...]) -> str:
    """Menú numerado de acciones legales, con etiquetas claras."""
    lineas = ["  ¿Qué hacés?"]
    lineas.extend(f"     [{i}] {_label_accion(a)}" for i, a in enumerate(acciones))
    return "\n".join(lineas)


def resumen_ronda(estado: EstadoRonda, humano: int = 0) -> list[str]:
    """Resumen al cerrar una ronda: puntos de envido, de truco y quién ganó."""
    lineas = [_LINEA, "  FIN DE LA MANO"]

    if estado.envido_resuelto and estado.envido_ganador is not None:
        g = estado.envido_ganador
        lineas.append(f"  · Envido: +{estado.puntos_envido} para {_quien(g, humano)}")

    if estado.ganador is not None:
        g = estado.ganador
        envido_a_g = estado.puntos_envido if estado.envido_ganador == g else 0
        pts_truco = estado.puntos_ronda[g] - envido_a_g
        motivo = {
            "bazas": "por las cartas",
            "no_quiero_truco": "no quisieron el truco",
            "mazo": "se fueron al mazo",
        }.get(estado.motivo, estado.motivo)
        if pts_truco > 0:
            lineas.append(f"  · Truco:  +{pts_truco} para {_quien(g, humano)}  ({motivo})")
        lineas.append(f"  → Ganó la mano: {_quien(g, humano)}")

    lineas.append(
        f"  Puntos de la ronda:  vos +{estado.puntos_ronda[humano]}  "
        f"—  +{estado.puntos_ronda[1 - humano]} la máquina"
    )
    lineas.append(_LINEA)
    return lineas


def encabezado_ronda(numero: int, mano: int, humano: int = 0) -> str:
    """Título al empezar una ronda."""
    quien_mano = "vos" if mano == humano else "la máquina"
    return f"\n╔═ Mano #{numero} — arranca {quien_mano} (es mano) ═╗"


def resumen_partida(puntos: tuple[int, int], objetivo: int, humano: int = 0) -> str:
    """Cartel de cierre de la partida."""
    yo = puntos[humano]
    otro = puntos[1 - humano]
    titulo = "🏆  ¡GANASTE LA PARTIDA!" if yo > otro else "🤖  Ganó la máquina."
    return f"\n{_LINEA}\n  {titulo}\n  Marcador final:  vos {yo}  —  {otro} la máquina\n{_LINEA}"
