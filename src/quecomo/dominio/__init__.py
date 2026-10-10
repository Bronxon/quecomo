"""Capa de DOMINIO: conceptos del negocio y sus reglas.

Esta capa no depende de Gradio, de la base de datos ni de ningún detalle
técnico. Todo lo que aquí vive puede probarse de forma aislada.
"""

from .entidades import (
    Evaluacion,
    Horario,
    Menu,
    Producto,
    Promocion,
    Restaurante,
    Transaccion,
    Ubicacion,
    Usuario,
)
from .estados import (
    EstadoEvaluacion,
    EstadoRestaurante,
    EstadoTransaccion,
    EstadoUsuario,
    Rol,
)
from .excepciones import (
    DatosInvalidos,
    EntidadNoEncontrada,
    ErrorDominio,
    EvaluacionNoPermitida,
    OperacionNoAutorizada,
    TransicionInvalida,
)

__all__ = [
    "DatosInvalidos",
    "EntidadNoEncontrada",
    "ErrorDominio",
    "EstadoEvaluacion",
    "EstadoRestaurante",
    "EstadoTransaccion",
    "EstadoUsuario",
    "Evaluacion",
    "EvaluacionNoPermitida",
    "Horario",
    "Menu",
    "OperacionNoAutorizada",
    "Producto",
    "Promocion",
    "Restaurante",
    "Rol",
    "Transaccion",
    "TransicionInvalida",
    "Ubicacion",
    "Usuario",
]
