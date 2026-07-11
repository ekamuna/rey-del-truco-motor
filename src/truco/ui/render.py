"""Formateo de texto de la partida para la terminal."""

from __future__ import annotations

from truco.core.cards import Carta
from truco.core.state import EstadoObservable, ResultadoBaza


def marcador_bazas(obs: EstadoObservable) -> tuple[int, int]:
    """Cuántas bazas ganó (yo, rival). Las pardas no cuentan para ninguno."""
    mias = sum(1 for b in obs.bazas if b.ganador == obs.jugador)
    rival = sum(1 for b in obs.bazas if b.ganador is not None and b.ganador != obs.jugador)
    return mias, rival


def formato_observacion(obs: EstadoObservable) -> str:
    """Arma el texto de lo que ve el jugador: rol, marcador, mesa y su mano."""
    rol = "MANO" if obs.soy_mano else "PIE"
    mias, rival = marcador_bazas(obs)
    lineas = [
        f"── Sos el jugador {obs.jugador} ({rol}) ──",
        f"Bazas ganadas: vos {mias} - {rival} rival",
    ]

    carta_rival = obs.mesa[1 - obs.jugador]
    if carta_rival is not None:
        lineas.append(f"El rival jugó: {carta_rival}")
    else:
        lineas.append("El rival todavía no jugó esta baza.")

    lineas.append("Tus cartas:")
    lineas.extend(f"  [{i}] {carta}" for i, carta in enumerate(obs.mi_mano))
    return "\n".join(lineas)


def formato_baza(baza: ResultadoBaza) -> str:
    """Describe el resultado de una baza recién cerrada."""
    if baza.ganador is None:
        return "  ⇒ parda"
    return f"  ⇒ gana la baza el jugador {baza.ganador}"


def formato_jugada(jugador: int, carta: Carta) -> str:
    return f"  → el jugador {jugador} juega {carta}"
