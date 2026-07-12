"""Formateo de texto de la partida para la terminal."""

from __future__ import annotations

from truco.core.acciones import Accion
from truco.core.state import EstadoObservable, ResultadoBaza


def marcador_bazas(obs: EstadoObservable) -> tuple[int, int]:
    """Cuántas bazas ganó (yo, rival). Las pardas no cuentan para ninguno."""
    mias = sum(1 for b in obs.bazas if b.ganador == obs.jugador)
    rival = sum(1 for b in obs.bazas if b.ganador is not None and b.ganador != obs.jugador)
    return mias, rival


def formato_observacion(obs: EstadoObservable) -> str:
    """Arma el texto de lo que ve el jugador."""
    rol = "MANO" if obs.soy_mano else "PIE"
    mias, rival = marcador_bazas(obs)
    yo, otro = obs.puntos_partida[obs.jugador], obs.puntos_partida[1 - obs.jugador]
    lineas = [
        f"── Jugador {obs.jugador} ({rol}) · partida a {obs.objetivo} ──",
        f"Partida: vos {yo} - {otro} rival   |   Bazas: {mias} - {rival}",
    ]

    if obs.pendiente is not None:
        cadena = " → ".join(c.value for c in obs.pendiente.cantos)
        lineas.append(f"⚠ Canto pendiente: {cadena}  (tenés que responder)")

    carta_rival = obs.mesa[1 - obs.jugador]
    if carta_rival is not None:
        lineas.append(f"El rival jugó: {carta_rival}")

    lineas.append(f"Tus cartas (tu envido: {obs.mi_tanto}):")
    lineas.extend(f"  {c}" for c in obs.mi_mano)
    return "\n".join(lineas)


def formato_menu(acciones: tuple[Accion, ...]) -> str:
    """Lista numerada de acciones legales para elegir."""
    return "\n".join(f"  [{i}] {a}" for i, a in enumerate(acciones))


def formato_baza(baza: ResultadoBaza) -> str:
    if baza.ganador is None:
        return "  ⇒ parda"
    return f"  ⇒ gana la baza el jugador {baza.ganador}"


def formato_accion(jugador: int, accion: Accion) -> str:
    return f"  → jugador {jugador}: {accion}"
