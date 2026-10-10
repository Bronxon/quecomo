"""Repositorios en memoria.

Son suficientes para el MVP y las pruebas. Al reiniciar la aplicación los
datos vuelven al estado de demostración. Para persistir, basta con crear
otras clases que implementen los mismos contratos de
``quecomo.dominio.repositorios`` (por ejemplo, con SQLite).

Cada repositorio usa un candado (``RLock``) porque Gradio atiende varias
solicitudes en hilos distintos.
"""

from __future__ import annotations

import itertools
import threading
from typing import Generic, TypeVar

from ..dominio.entidades import Evaluacion, Restaurante, Transaccion, Usuario
from ..dominio.excepciones import DatosInvalidos
from ..dominio.repositorios import (
    IRepositorioEvaluaciones,
    IRepositorioRestaurantes,
    IRepositorioTransacciones,
    IRepositorioUsuarios,
)

T = TypeVar("T")


class _AlmacenMemoria(Generic[T]):
    def __init__(self) -> None:
        self._datos: dict[int, T] = {}
        self._candado = threading.RLock()
        self._contador = itertools.count(1)

    def _obtener(self, entidad_id: int) -> T | None:
        with self._candado:
            return self._datos.get(entidad_id)

    def _listar(self) -> list[T]:
        with self._candado:
            return [self._datos[k] for k in sorted(self._datos)]

    def _guardar(self, entidad_id: int, entidad: T) -> None:
        with self._candado:
            self._datos[entidad_id] = entidad

    def siguiente_id(self) -> int:
        with self._candado:
            while True:
                candidato = next(self._contador)
                if candidato not in self._datos:
                    return candidato


class RepositorioUsuariosMemoria(_AlmacenMemoria[Usuario], IRepositorioUsuarios):
    def obtener(self, usuario_id: int) -> Usuario | None:
        return self._obtener(usuario_id)

    def listar(self) -> list[Usuario]:
        return self._listar()

    def guardar(self, usuario: Usuario) -> None:
        self._guardar(usuario.id, usuario)


class RepositorioRestaurantesMemoria(_AlmacenMemoria[Restaurante], IRepositorioRestaurantes):
    def obtener(self, restaurante_id: int) -> Restaurante | None:
        return self._obtener(restaurante_id)

    def listar(self) -> list[Restaurante]:
        return self._listar()

    def listar_por_locatario(self, locatario_id: int) -> list[Restaurante]:
        return [r for r in self._listar() if r.locatario_id == locatario_id]

    def guardar(self, restaurante: Restaurante) -> None:
        self._guardar(restaurante.id, restaurante)


class RepositorioTransaccionesMemoria(_AlmacenMemoria[Transaccion], IRepositorioTransacciones):
    def obtener(self, transaccion_id: int) -> Transaccion | None:
        return self._obtener(transaccion_id)

    def buscar_por_usuario_y_restaurante(
        self, usuario_id: int, restaurante_id: int
    ) -> list[Transaccion]:
        return [
            t
            for t in self._listar()
            if t.usuario_id == usuario_id and t.restaurante_id == restaurante_id
        ]

    def listar_por_usuario(self, usuario_id: int) -> list[Transaccion]:
        return [t for t in self._listar() if t.usuario_id == usuario_id]

    def listar_por_restaurante(self, restaurante_id: int) -> list[Transaccion]:
        return [t for t in self._listar() if t.restaurante_id == restaurante_id]

    def guardar(self, transaccion: Transaccion) -> None:
        self._guardar(transaccion.id, transaccion)


class RepositorioEvaluacionesMemoria(_AlmacenMemoria[Evaluacion], IRepositorioEvaluaciones):
    def obtener(self, evaluacion_id: int) -> Evaluacion | None:
        return self._obtener(evaluacion_id)

    def obtener_por_restaurante(
        self, restaurante_id: int, incluir_ocultas: bool = False
    ) -> list[Evaluacion]:
        return [
            e
            for e in self._listar()
            if e.restaurante_id == restaurante_id and (incluir_ocultas or e.esta_publicada)
        ]

    def obtener_por_transaccion(self, transaccion_id: int) -> Evaluacion | None:
        return next((e for e in self._listar() if e.transaccion_id == transaccion_id), None)

    def listar(self) -> list[Evaluacion]:
        return self._listar()

    def guardar(self, evaluacion: Evaluacion) -> None:
        with self._candado:
            existente = self.obtener_por_transaccion(evaluacion.transaccion_id)
            if existente is not None and existente.id != evaluacion.id:
                # Restricción de unicidad: 1 Transacción → 0..1 Evaluación.
                raise DatosInvalidos(
                    f"La transacción #{evaluacion.transaccion_id} ya tiene una evaluación."
                )
            self._guardar(evaluacion.id, evaluacion)
