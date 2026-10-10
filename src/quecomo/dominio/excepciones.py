"""Excepciones del dominio.

Las reglas de negocio se expresan lanzando excepciones con un mensaje
comprensible para la persona usuaria. La capa de presentación las captura y
las muestra; nunca decide por sí misma si una operación es válida.
"""

from __future__ import annotations

from enum import Enum


class ErrorDominio(Exception):
    """Base de todos los errores de negocio de ¿Qué Como?."""


class DatosInvalidos(ErrorDominio):
    """Los datos proporcionados no cumplen las validaciones."""


class TransicionInvalida(ErrorDominio):
    """Se intentó un cambio de estado no permitido por la máquina de estados."""


class OperacionNoAutorizada(ErrorDominio):
    """El actor no tiene permiso para realizar la operación (CA-08)."""


class EntidadNoEncontrada(ErrorDominio):
    """No existe la entidad solicitada."""


class MotivoRechazo(str, Enum):
    """Motivos por los que se rechaza una evaluación (extensiones de CU-01)."""

    SIN_TRANSACCION = "SIN_TRANSACCION"
    TRANSACCION_AJENA = "TRANSACCION_AJENA"
    TRANSACCION_NO_COMPLETADA = "TRANSACCION_NO_COMPLETADA"
    TRANSACCION_CANCELADA = "TRANSACCION_CANCELADA"
    TRANSACCION_YA_EVALUADA = "TRANSACCION_YA_EVALUADA"
    RESTAURANTE_NO_DISPONIBLE = "RESTAURANTE_NO_DISPONIBLE"
    USUARIO_NO_HABILITADO = "USUARIO_NO_HABILITADO"


class EvaluacionNoPermitida(ErrorDominio):
    """La evaluación no puede registrarse (RN-01, RN-05, RN-06)."""

    def __init__(self, motivo: MotivoRechazo, mensaje: str) -> None:
        super().__init__(mensaje)
        self.motivo = motivo
