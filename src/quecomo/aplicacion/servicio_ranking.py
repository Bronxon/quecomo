"""Cálculo del ranking a partir de evaluaciones válidas (RF-10).

El ranking se calcula en el momento de la consulta: solo cuentan las
evaluaciones PUBLICADAS, y toda evaluación está respaldada por una
transacción COMPLETADA, por lo que el ranking hereda esa trazabilidad.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from ..dominio.repositorios import IRepositorioEvaluaciones

#: Parámetros del promedio ponderado usado para ORDENAR resultados.
#: Evitan que un restaurante con una sola evaluación de 5 ★ supere a otro
#: con muchas evaluaciones de 4.8 ★. Es una decisión de diseño ajustable.
PESO_PREVIO = 2
CALIFICACION_PREVIA = 3.0


@dataclass(frozen=True)
class Ranking:
    promedio: float | None
    total: int
    distribucion: dict[int, int]
    puntaje: float = CALIFICACION_PREVIA
    """Promedio ponderado (bayesiano) para ordenar; no se muestra como calificación."""

    @property
    def tiene_evaluaciones(self) -> bool:
        return self.total > 0

    def texto(self) -> str:
        if not self.tiene_evaluaciones:
            return "Sin evaluaciones"
        return f"{self.promedio:.1f} ★ ({self.total})"


class ServicioRanking:
    def __init__(self, evaluaciones: IRepositorioEvaluaciones) -> None:
        self._evaluaciones = evaluaciones

    def calcular(self, restaurante_id: int) -> Ranking:
        validas = self._evaluaciones.obtener_por_restaurante(restaurante_id)
        conteo = Counter(e.calificacion for e in validas)
        distribucion = {estrellas: conteo.get(estrellas, 0) for estrellas in range(5, 0, -1)}
        if not validas:
            return Ranking(promedio=None, total=0, distribucion=distribucion)
        suma = sum(e.calificacion for e in validas)
        promedio = suma / len(validas)
        puntaje = (PESO_PREVIO * CALIFICACION_PREVIA + suma) / (PESO_PREVIO + len(validas))
        return Ranking(
            promedio=round(promedio, 2),
            total=len(validas),
            distribucion=distribucion,
            puntaje=round(puntaje, 4),
        )
