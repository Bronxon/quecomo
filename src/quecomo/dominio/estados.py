"""Estados y roles del dominio.

La máquina de estados de la Transacción corresponde a la sección 10.3 del
Documento Fundamental:

    INICIADA → PENDIENTE → CONFIRMADA → COMPLETADA
                   │            │
                   └──────┬─────┘
                          ▼
                      CANCELADA

COMPLETADA y CANCELADA son estados finales. En particular, la transición
CANCELADA → COMPLETADA es inválida.
"""

from __future__ import annotations

from enum import Enum


class EstadoTransaccion(str, Enum):
    """Ciclo de vida de una transacción (relación comercial)."""

    INICIADA = "INICIADA"
    PENDIENTE = "PENDIENTE"
    CONFIRMADA = "CONFIRMADA"
    COMPLETADA = "COMPLETADA"
    CANCELADA = "CANCELADA"

    @property
    def es_final(self) -> bool:
        return not TRANSICIONES_TRANSACCION[self]


#: Transiciones permitidas. Cualquier otra se rechaza con ``TransicionInvalida``.
TRANSICIONES_TRANSACCION: dict[EstadoTransaccion, frozenset[EstadoTransaccion]] = {
    EstadoTransaccion.INICIADA: frozenset({EstadoTransaccion.PENDIENTE}),
    EstadoTransaccion.PENDIENTE: frozenset(
        {EstadoTransaccion.CONFIRMADA, EstadoTransaccion.CANCELADA}
    ),
    EstadoTransaccion.CONFIRMADA: frozenset(
        {EstadoTransaccion.COMPLETADA, EstadoTransaccion.CANCELADA}
    ),
    EstadoTransaccion.COMPLETADA: frozenset(),
    EstadoTransaccion.CANCELADA: frozenset(),
}


class EstadoRestaurante(str, Enum):
    """Disponibilidad del restaurante en la plataforma."""

    ACTIVO = "ACTIVO"
    SUSPENDIDO = "SUSPENDIDO"


class EstadoUsuario(str, Enum):
    ACTIVO = "ACTIVO"
    BLOQUEADO = "BLOQUEADO"


class EstadoEvaluacion(str, Enum):
    """Una evaluación OCULTA (moderada) no cuenta para el ranking."""

    PUBLICADA = "PUBLICADA"
    OCULTA = "OCULTA"


class Rol(str, Enum):
    """Actores del ecosistema (sección 2.1)."""

    CLIENTE = "CLIENTE"
    LOCATARIO = "LOCATARIO"
    ADMINISTRADOR = "ADMINISTRADOR"

    @property
    def etiqueta(self) -> str:
        return {
            Rol.CLIENTE: "Cliente",
            Rol.LOCATARIO: "Locatario",
            Rol.ADMINISTRADOR: "Administrador",
        }[self]
