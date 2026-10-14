
"""Adapter que convierte registros JSON al modelo de dominio."""

from __future__ import annotations

import json
from datetime import date, time
from decimal import Decimal
from pathlib import Path
from typing import Any, Protocol

from ..dominio.entidades import Horario, Restaurante, Ubicacion
from ..dominio.estados import EstadoRestaurante


class ErrorFormatoRestaurantes(ValueError):
    """El archivo o registro no cumple el formato esperado."""


class FuenteRestaurantes(Protocol):
    """Contrato destino para fuentes de datos de restaurantes."""

    def cargar(self) -> list[Restaurante]:
        """Devuelve restaurantes en el modelo de dominio."""


class AdapterRestaurantesJSON:
    """Adapta una fuente JSON al contrato FuenteRestaurantes."""

    def __init__(self, ruta: str | Path) -> None:
        self._ruta = Path(ruta)

    def cargar(self) -> list[Restaurante]:
        """Carga el archivo y adapta sus registros."""
        return self.cargar_archivo(self._ruta)

    @staticmethod
    def convertir(registro: dict[str, Any]) -> Restaurante:
        """Convierte un registro externo en una entidad Restaurante."""
        try:
            ubicacion = registro["ubicacion"]
            horario = registro["horario"]

            return Restaurante(
                id=int(registro["id"]),
                nombre=str(registro["nombre"]),
                descripcion=str(registro["descripcion"]),
                categoria=str(registro["categoria"]),
                ubicacion=Ubicacion(
                    direccion=str(ubicacion["direccion"]),
                    latitud=float(ubicacion["latitud"]),
                    longitud=float(ubicacion["longitud"]),
                    zona=str(ubicacion.get("zona", "")),
                ),
                horario=Horario(
                    dias=frozenset(int(d) for d in horario["dias"]),
                    apertura=time.fromisoformat(horario["apertura"]),
                    cierre=time.fromisoformat(horario["cierre"]),
                ),
                formas_pago=frozenset(registro["formas_pago"]),
                precio_promedio=Decimal(str(registro["precio_promedio"])),
                fecha_apertura=date.fromisoformat(registro["fecha_apertura"]),
                locatario_id=int(registro["locatario_id"]),
                estado=EstadoRestaurante(
                    registro.get("estado", EstadoRestaurante.ACTIVO.value)
                ),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ErrorFormatoRestaurantes(
                f"Registro de restaurante inválido: {error}"
            ) from error

    @classmethod
    def cargar_archivo(cls, ruta: str | Path) -> list[Restaurante]:
        """Lee un arreglo JSON y adapta cada restaurante."""
        try:
            with Path(ruta).open(encoding="utf-8") as archivo:
                registros = json.load(archivo)
        except (OSError, json.JSONDecodeError) as error:
            raise ErrorFormatoRestaurantes(
                f"No se pudo leer el archivo JSON: {error}"
            ) from error

        if not isinstance(registros, list):
            raise ErrorFormatoRestaurantes(
                "El archivo debe contener una lista JSON de restaurantes."
            )

        return [cls.convertir(registro) for registro in registros]
