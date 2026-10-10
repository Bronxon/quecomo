"""Raíz de composición: aquí se «arma» la aplicación.

Es el único lugar que conoce las implementaciones concretas de los
repositorios. Para cambiar a una base de datos real, basta con sustituirlas
en ``crear_aplicacion``.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .aplicacion.controlador_evaluacion import ControladorEvaluacion
from .aplicacion.servicio_busqueda import PuntoReferencia, ServicioBusqueda
from .aplicacion.servicio_ranking import ServicioRanking
from .aplicacion.servicio_restaurantes import ServicioRestaurantes
from .aplicacion.servicio_transacciones import ServicioTransacciones
from .dominio.repositorios import (
    IRepositorioEvaluaciones,
    IRepositorioRestaurantes,
    IRepositorioTransacciones,
    IRepositorioUsuarios,
)
from .infraestructura.datos_demo import PUNTOS_REFERENCIA, cargar_datos_demo
from .infraestructura.memoria import (
    RepositorioEvaluacionesMemoria,
    RepositorioRestaurantesMemoria,
    RepositorioTransaccionesMemoria,
    RepositorioUsuariosMemoria,
)

#: Zona horaria usada para «abierto ahora». Se puede cambiar con la
#: variable de entorno ``QUECOMO_ZONA_HORARIA``.
ZONA_HORARIA_PREDETERMINADA = "America/Hermosillo"


def reloj_local(zona: str | None = None) -> Callable[[], datetime]:
    """Devuelve una función que da la hora local (sin zona) del negocio."""
    nombre = zona or os.getenv("QUECOMO_ZONA_HORARIA", ZONA_HORARIA_PREDETERMINADA)
    try:
        tz = ZoneInfo(nombre)
    except ZoneInfoNotFoundError:
        tz = None
    return lambda: datetime.now(tz).replace(tzinfo=None)


@dataclass
class Aplicacion:
    """Agrupa repositorios y servicios ya conectados entre sí."""

    usuarios: IRepositorioUsuarios
    restaurantes: IRepositorioRestaurantes
    transacciones: IRepositorioTransacciones
    evaluaciones: IRepositorioEvaluaciones
    reloj: Callable[[], datetime]
    ranking: ServicioRanking = field(init=False)
    busqueda: ServicioBusqueda = field(init=False)
    controlador_evaluacion: ControladorEvaluacion = field(init=False)
    servicio_transacciones: ServicioTransacciones = field(init=False)
    servicio_restaurantes: ServicioRestaurantes = field(init=False)
    puntos_referencia: list[PuntoReferencia] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.ranking = ServicioRanking(self.evaluaciones)
        self.busqueda = ServicioBusqueda(self.restaurantes, self.ranking, self.reloj)
        self.controlador_evaluacion = ControladorEvaluacion(
            self.usuarios, self.restaurantes, self.transacciones, self.evaluaciones, self.reloj
        )
        self.servicio_transacciones = ServicioTransacciones(
            self.usuarios, self.restaurantes, self.transacciones, self.reloj
        )
        self.servicio_restaurantes = ServicioRestaurantes(
            self.usuarios, self.restaurantes, self.evaluaciones, self.reloj
        )

    def punto(self, nombre: str | None) -> PuntoReferencia | None:
        return next((p for p in self.puntos_referencia if p.nombre == nombre), None)


def crear_aplicacion(
    datos_demo: bool = True, reloj: Callable[[], datetime] | None = None
) -> Aplicacion:
    reloj = reloj or reloj_local()
    app = Aplicacion(
        usuarios=RepositorioUsuariosMemoria(),
        restaurantes=RepositorioRestaurantesMemoria(),
        transacciones=RepositorioTransaccionesMemoria(),
        evaluaciones=RepositorioEvaluacionesMemoria(),
        reloj=reloj,
        puntos_referencia=[PuntoReferencia(n, lat, lon) for n, lat, lon in PUNTOS_REFERENCIA],
    )
    if datos_demo:
        cargar_datos_demo(
            app.usuarios, app.restaurantes, app.transacciones, app.evaluaciones, reloj()
        )
    return app
