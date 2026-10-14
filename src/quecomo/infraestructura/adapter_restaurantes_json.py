
"""Adapter GoF: traduce registros JSON al modelo de dominio."""

from __future__ import annotations

import json
from datetime import date, time
from decimal import Decimal
from pathlib import Path
from typing import Any

from ..dominio.entidades import Horario, Restaurante, Ubicacion
from ..dominio.estados import EstadoRestaurante


class ErrorFormatoRestaurantes(ValueError):
    """El archivo JSON no cumple el formato esperado."""


class AdapterRestaurantesJSON:
    """Adapta el formato externo JSON al modelo de ¿Qué Como?."""

    @staticmethod
    def convertir(registro: dict[str, Any]) -> Restaurante:
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
        """Carga un arreglo JSON y adapta cada registro."""
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
