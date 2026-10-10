"""Contratos de repositorio (sección 8.1).

El dominio define *qué* necesita guardar o consultar; la infraestructura
decide *cómo* (memoria, SQLite, PostgreSQL...). Esto mantiene bajo el
acoplamiento: cambiar la base de datos no obliga a tocar las reglas.

Equivalencias con el Documento Fundamental:

- ``IRepositorioTransacciones.buscarPorUsuarioYEstablecimiento(...)``
  → ``buscar_por_usuario_y_restaurante(usuario_id, restaurante_id)``
- ``IRepositorioEvaluaciones.guardar(evaluacion)`` → ``guardar(evaluacion)``
- ``IRepositorioEvaluaciones.obtenerPorEstablecimiento(id)``
  → ``obtener_por_restaurante(restaurante_id)``
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .entidades import Evaluacion, Restaurante, Transaccion, Usuario


class IRepositorioUsuarios(ABC):
    @abstractmethod
    def obtener(self, usuario_id: int) -> Usuario | None: ...

    @abstractmethod
    def listar(self) -> list[Usuario]: ...

    @abstractmethod
    def guardar(self, usuario: Usuario) -> None: ...

    @abstractmethod
    def siguiente_id(self) -> int: ...


class IRepositorioRestaurantes(ABC):
    @abstractmethod
    def obtener(self, restaurante_id: int) -> Restaurante | None: ...

    @abstractmethod
    def listar(self) -> list[Restaurante]: ...

    @abstractmethod
    def listar_por_locatario(self, locatario_id: int) -> list[Restaurante]: ...

    @abstractmethod
    def guardar(self, restaurante: Restaurante) -> None: ...

    @abstractmethod
    def siguiente_id(self) -> int: ...


class IRepositorioTransacciones(ABC):
    @abstractmethod
    def obtener(self, transaccion_id: int) -> Transaccion | None: ...

    @abstractmethod
    def buscar_por_usuario_y_restaurante(
        self, usuario_id: int, restaurante_id: int
    ) -> list[Transaccion]: ...

    @abstractmethod
    def listar_por_usuario(self, usuario_id: int) -> list[Transaccion]: ...

    @abstractmethod
    def listar_por_restaurante(self, restaurante_id: int) -> list[Transaccion]: ...

    @abstractmethod
    def guardar(self, transaccion: Transaccion) -> None: ...

    @abstractmethod
    def siguiente_id(self) -> int: ...


class IRepositorioEvaluaciones(ABC):
    @abstractmethod
    def obtener(self, evaluacion_id: int) -> Evaluacion | None: ...

    @abstractmethod
    def obtener_por_restaurante(
        self, restaurante_id: int, incluir_ocultas: bool = False
    ) -> list[Evaluacion]: ...

    @abstractmethod
    def obtener_por_transaccion(self, transaccion_id: int) -> Evaluacion | None: ...

    @abstractmethod
    def listar(self) -> list[Evaluacion]: ...

    @abstractmethod
    def guardar(self, evaluacion: Evaluacion) -> None:
        """Debe rechazar una segunda evaluación para la misma transacción
        (equivalente a una restricción UNIQUE en base de datos, RN-06)."""

    @abstractmethod
    def siguiente_id(self) -> int: ...
