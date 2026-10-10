"""Búsqueda, filtrado y comparación de restaurantes (HU-01 a HU-05).

Criterios del Vision Statement: precio, calidad (ranking), distancia,
horario, ubicación, menú, promociones, formas de pago y antigüedad.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum

from ..dominio.entidades import Restaurante
from ..dominio.excepciones import DatosInvalidos
from ..dominio.repositorios import IRepositorioRestaurantes
from .servicio_ranking import Ranking, ServicioRanking

MAXIMO_COMPARACION = 3


class Orden(str, Enum):
    RANKING = "Mejor ranking"
    DISTANCIA = "Más cercano"
    PRECIO = "Menor precio"
    ANTIGUEDAD = "Más antigüedad"


@dataclass(frozen=True)
class PuntoReferencia:
    nombre: str
    latitud: float
    longitud: float


@dataclass
class CriteriosBusqueda:
    """Todos los campos son opcionales: ``None`` significa «sin filtro»."""

    texto: str = ""
    categoria: str | None = None
    precio_maximo: float | None = None
    punto: PuntoReferencia | None = None
    distancia_maxima_km: float | None = None
    abierto_en: datetime | None = None
    forma_pago: str | None = None
    calificacion_minima: float | None = None
    solo_con_promocion: bool = False
    orden: Orden = Orden.RANKING


@dataclass(frozen=True)
class ResultadoBusqueda:
    restaurante: Restaurante
    ranking: Ranking
    distancia_km: float | None
    abierto: bool
    promociones_vigentes: int
    antiguedad_anios: int


def _normalizar(texto: str) -> str:
    """Minúsculas y sin acentos, para que «Cafe» encuentre «Café»."""
    descompuesto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


class ServicioBusqueda:
    def __init__(
        self,
        restaurantes: IRepositorioRestaurantes,
        ranking: ServicioRanking,
        reloj: Callable[[], datetime] = datetime.now,
    ) -> None:
        self._restaurantes = restaurantes
        self._ranking = ranking
        self._reloj = reloj

    # -- Catálogos para los filtros --------------------------------------- #

    def categorias(self) -> list[str]:
        return sorted({r.categoria for r in self._disponibles()})

    def formas_pago(self) -> list[str]:
        return sorted({f for r in self._disponibles() for f in r.formas_pago})

    def restaurantes_disponibles(self) -> list[Restaurante]:
        return sorted(self._disponibles(), key=lambda r: r.nombre)

    # -- HU-01 / HU-02 / HU-05 -------------------------------------------- #

    def buscar(self, criterios: CriteriosBusqueda) -> list[ResultadoBusqueda]:
        ahora = self._reloj()
        resultados = [self._resumir(r, criterios.punto, criterios.abierto_en or ahora)
                      for r in self._disponibles()]
        resultados = [r for r in resultados if self._cumple(r, criterios)]
        return self._ordenar(resultados, criterios.orden)

    # -- HU-03 ------------------------------------------------------------ #

    def detalle(self, restaurante_id: int, punto: PuntoReferencia | None = None) -> ResultadoBusqueda:
        restaurante = self._restaurantes.obtener(int(restaurante_id))
        if restaurante is None or not restaurante.esta_disponible():
            raise DatosInvalidos("El restaurante no existe o no está disponible.")
        return self._resumir(restaurante, punto, self._reloj())

    # -- HU-04 ------------------------------------------------------------ #

    def comparar(
        self, restaurante_ids: list[int], punto: PuntoReferencia | None = None
    ) -> list[ResultadoBusqueda]:
        ids = list(dict.fromkeys(int(i) for i in restaurante_ids))
        if len(ids) < 2:
            raise DatosInvalidos("Selecciona al menos dos restaurantes para comparar.")
        if len(ids) > MAXIMO_COMPARACION:
            raise DatosInvalidos(f"Puedes comparar como máximo {MAXIMO_COMPARACION} restaurantes.")
        return [self.detalle(i, punto) for i in ids]

    # -- Auxiliares ------------------------------------------------------- #

    def _disponibles(self) -> list[Restaurante]:
        return [r for r in self._restaurantes.listar() if r.esta_disponible()]

    def _resumir(
        self, restaurante: Restaurante, punto: PuntoReferencia | None, momento: datetime
    ) -> ResultadoBusqueda:
        distancia = (
            restaurante.ubicacion.distancia_km(punto.latitud, punto.longitud) if punto else None
        )
        return ResultadoBusqueda(
            restaurante=restaurante,
            ranking=self._ranking.calcular(restaurante.id),
            distancia_km=round(distancia, 2) if distancia is not None else None,
            abierto=restaurante.horario.esta_abierto(momento),
            promociones_vigentes=len(restaurante.promociones_vigentes(momento.date())),
            antiguedad_anios=restaurante.antiguedad_anios(momento.date()),
        )

    @staticmethod
    def _cumple(resultado: ResultadoBusqueda, c: CriteriosBusqueda) -> bool:
        r = resultado.restaurante
        if c.texto:
            buscado = _normalizar(c.texto.strip())
            campos = [r.nombre, r.descripcion, r.categoria, *(p.nombre for p in r.productos())]
            if not any(buscado in _normalizar(campo) for campo in campos):
                return False
        if c.categoria and r.categoria != c.categoria:
            return False
        if c.precio_maximo is not None and r.precio_promedio > Decimal(str(c.precio_maximo)):
            return False
        if (
            c.distancia_maxima_km is not None
            and resultado.distancia_km is not None
            and resultado.distancia_km > c.distancia_maxima_km
        ):
            return False
        if c.abierto_en is not None and not resultado.abierto:
            return False
        if c.forma_pago and not r.acepta_pago(c.forma_pago):
            return False
        if c.calificacion_minima:
            promedio = resultado.ranking.promedio
            if promedio is None or promedio < c.calificacion_minima:
                return False
        if c.solo_con_promocion and resultado.promociones_vigentes == 0:
            return False
        return True

    @staticmethod
    def _ordenar(resultados: list[ResultadoBusqueda], orden: Orden) -> list[ResultadoBusqueda]:
        if orden is Orden.DISTANCIA:
            clave = lambda x: (x.distancia_km is None, x.distancia_km or 0, x.restaurante.nombre)  # noqa: E731
        elif orden is Orden.PRECIO:
            clave = lambda x: (x.restaurante.precio_promedio, x.restaurante.nombre)  # noqa: E731
        elif orden is Orden.ANTIGUEDAD:
            clave = lambda x: (-x.antiguedad_anios, x.restaurante.nombre)  # noqa: E731
        else:  # RANKING: promedio ponderado; sin evaluaciones al final
            clave = lambda x: (  # noqa: E731
                x.ranking.promedio is None,
                -x.ranking.puntaje,
                -x.ranking.total,
                x.restaurante.nombre,
            )
        return sorted(resultados, key=clave)
