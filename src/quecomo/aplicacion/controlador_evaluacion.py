"""ControladorEvaluacion — realización del caso de uso CU-01.

«Evaluar restaurante después de una transacción» (secciones 5, 7 y 10).

GRASP Controller: recibe la solicitud y coordina a los objetos del dominio,
pero **no** decide si una transacción puede evaluarse; esa decisión la toma
la propia ``Transaccion`` (Information Expert).

Secuencia implementada (sección 10.1):

1. Usuario → Controlador: ``solicitar_evaluacion(usuario_id, transaccion_id)``
2. Controlador → RepositorioTransacciones: buscar la transacción
3. Repositorio → Controlador: ``transaccion``
4. Controlador → Transaccion: ``puede_evaluarse()``
5. Transaccion → Controlador: true / false (con motivo)
6. Si es válida: ``Evaluacion.crear(...)``
7. Evaluacion: ``validar()``
8. Controlador → RepositorioEvaluaciones: ``guardar(evaluacion)``
9. Repositorio → Controlador: confirmación
10. Controlador → Usuario: evaluación registrada
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from datetime import datetime

from ..dominio.entidades import Evaluacion, Restaurante, Transaccion, Usuario
from ..dominio.excepciones import EvaluacionNoPermitida, MotivoRechazo
from ..dominio.repositorios import (
    IRepositorioEvaluaciones,
    IRepositorioRestaurantes,
    IRepositorioTransacciones,
    IRepositorioUsuarios,
)


class ControladorEvaluacion:
    def __init__(
        self,
        usuarios: IRepositorioUsuarios,
        restaurantes: IRepositorioRestaurantes,
        transacciones: IRepositorioTransacciones,
        evaluaciones: IRepositorioEvaluaciones,
        reloj: Callable[[], datetime] = datetime.now,
    ) -> None:
        self._usuarios = usuarios
        self._restaurantes = restaurantes
        self._transacciones = transacciones
        self._evaluaciones = evaluaciones
        self._reloj = reloj
        # Evita que dos solicitudes simultáneas usen la misma transacción (RN-06).
        self._candado = threading.Lock()

    # ------------------------------------------------------------------ #
    # Consultas de apoyo
    # ------------------------------------------------------------------ #

    def transacciones_evaluables(
        self, usuario_id: int, restaurante_id: int | None = None
    ) -> list[Transaccion]:
        """Transacciones del usuario que hoy pueden respaldar una evaluación."""
        if restaurante_id is None:
            candidatas = self._transacciones.listar_por_usuario(usuario_id)
        else:
            candidatas = self._transacciones.buscar_por_usuario_y_restaurante(
                usuario_id, restaurante_id
            )
        return [t for t in candidatas if t.puede_evaluarse()]

    # ------------------------------------------------------------------ #
    # Pasos 1 a 6: validar la solicitud
    # ------------------------------------------------------------------ #

    def solicitar_evaluacion(self, usuario_id: int, transaccion_id: int | None) -> Transaccion:
        """Valida que la evaluación pueda iniciarse y devuelve la transacción.

        Lanza ``EvaluacionNoPermitida`` con el motivo concreto si no procede.
        """
        usuario = self._usuario_habilitado(usuario_id)
        transaccion = self._obtener_transaccion(transaccion_id)
        transaccion.verificar_evaluable_por(usuario.id)  # Information Expert
        self._restaurante_disponible(transaccion.restaurante_id)
        return transaccion

    # ------------------------------------------------------------------ #
    # Pasos 7 a 10: crear, validar, guardar y vincular
    # ------------------------------------------------------------------ #

    def registrar_evaluacion(
        self,
        usuario_id: int,
        transaccion_id: int | None,
        calificacion: int | float | str | None,
        comentario: str | None,
    ) -> Evaluacion:
        """Registra la evaluación. Repite todas las validaciones: nunca se
        confía en que la interfaz ya las haya hecho."""
        with self._candado:
            transaccion = self.solicitar_evaluacion(usuario_id, transaccion_id)
            restaurante = self._restaurante_disponible(transaccion.restaurante_id)

            evaluacion = Evaluacion.crear(
                id=self._evaluaciones.siguiente_id(),
                transaccion=transaccion,
                calificacion=calificacion,
                comentario=comentario,
                fecha=self._reloj(),
            )
            restaurante.recibir_evaluacion(evaluacion)

            self._evaluaciones.guardar(evaluacion)
            transaccion.vincular_evaluacion(evaluacion.id)
            self._transacciones.guardar(transaccion)
            return evaluacion

    # ------------------------------------------------------------------ #
    # Auxiliares
    # ------------------------------------------------------------------ #

    def _usuario_habilitado(self, usuario_id: int) -> Usuario:
        usuario = self._usuarios.obtener(usuario_id)
        if usuario is None or not usuario.esta_activo:
            raise EvaluacionNoPermitida(
                MotivoRechazo.USUARIO_NO_HABILITADO,
                "Debes iniciar sesión con una cuenta activa para evaluar.",
            )
        return usuario

    def _obtener_transaccion(self, transaccion_id: int | None) -> Transaccion:
        transaccion = (
            self._transacciones.obtener(int(transaccion_id)) if transaccion_id is not None else None
        )
        if transaccion is None:
            raise EvaluacionNoPermitida(
                MotivoRechazo.SIN_TRANSACCION,
                "No existe una transacción que respalde la evaluación. "
                "Se requiere una transacción válida con el restaurante.",
            )
        return transaccion

    def _restaurante_disponible(self, restaurante_id: int) -> Restaurante:
        restaurante = self._restaurantes.obtener(restaurante_id)
        if restaurante is None or not restaurante.esta_disponible():
            raise EvaluacionNoPermitida(
                MotivoRechazo.RESTAURANTE_NO_DISPONIBLE,
                "El restaurante no está disponible para recibir evaluaciones.",
            )
        return restaurante
