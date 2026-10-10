"""Registro y ciclo de vida de transacciones (HU-06, RF-05, CA-03, CA-08).

Control de quién puede mover el estado:

| Operación   | Transición                 | Quién puede hacerla              |
|-------------|----------------------------|----------------------------------|
| registrar   | INICIADA → PENDIENTE       | Cliente                          |
| confirmar   | PENDIENTE → CONFIRMADA     | Solo el locatario dueño          |
| completar   | CONFIRMADA → COMPLETADA    | Solo el locatario dueño          |
| cancelar    | PENDIENTE/CONFIRMADA → CANCELADA | Cliente dueño, locatario o administrador |

Así, el cliente **no** puede completar su propia transacción para
habilitarse una evaluación (requisito de Seguridad, sección 4.2), y el
administrador tampoco puede fabricar esa evidencia.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from decimal import Decimal

from ..dominio.entidades import Transaccion
from ..dominio.estados import Rol
from ..dominio.excepciones import (
    DatosInvalidos,
    EntidadNoEncontrada,
    OperacionNoAutorizada,
)
from ..dominio.repositorios import (
    IRepositorioRestaurantes,
    IRepositorioTransacciones,
    IRepositorioUsuarios,
)
from .autorizacion import (
    exigir_propietario,
    exigir_rol,
    obtener_restaurante,
    obtener_usuario_activo,
)

IMPORTE_MAXIMO = Decimal("100000")


class ServicioTransacciones:
    def __init__(
        self,
        usuarios: IRepositorioUsuarios,
        restaurantes: IRepositorioRestaurantes,
        transacciones: IRepositorioTransacciones,
        reloj: Callable[[], datetime] = datetime.now,
    ) -> None:
        self._usuarios = usuarios
        self._restaurantes = restaurantes
        self._transacciones = transacciones
        self._reloj = reloj

    # -- Cliente --------------------------------------------------------- #

    def registrar(
        self, usuario_id: int, restaurante_id: int | None, importe: object
    ) -> Transaccion:
        usuario = obtener_usuario_activo(self._usuarios, usuario_id)
        exigir_rol(usuario, Rol.CLIENTE)
        restaurante = obtener_restaurante(self._restaurantes, restaurante_id)
        if not restaurante.esta_disponible():
            raise DatosInvalidos(f"«{restaurante.nombre}» no está disponible.")

        ahora = self._reloj()
        transaccion = Transaccion(
            id=self._transacciones.siguiente_id(),
            usuario_id=usuario.id,
            restaurante_id=restaurante.id,
            importe=importe,
            fecha=ahora,
            actor_id=usuario.id,
        )
        if transaccion.importe > IMPORTE_MAXIMO:
            raise DatosInvalidos(f"El importe no puede superar ${IMPORTE_MAXIMO:,.2f}.")
        transaccion.enviar(ahora, usuario.id)
        self._transacciones.guardar(transaccion)
        return transaccion

    def listar_de_usuario(self, usuario_id: int) -> list[Transaccion]:
        usuario = obtener_usuario_activo(self._usuarios, usuario_id)
        return sorted(
            self._transacciones.listar_por_usuario(usuario.id), key=lambda t: t.id, reverse=True
        )

    # -- Locatario ------------------------------------------------------- #

    def listar_de_restaurante(self, actor_id: int, restaurante_id: int | None) -> list[Transaccion]:
        actor = obtener_usuario_activo(self._usuarios, actor_id)
        restaurante = obtener_restaurante(self._restaurantes, restaurante_id)
        exigir_propietario(actor, restaurante)
        return sorted(
            self._transacciones.listar_por_restaurante(restaurante.id),
            key=lambda t: t.id,
            reverse=True,
        )

    def confirmar(self, actor_id: int, transaccion_id: int | None) -> Transaccion:
        transaccion = self._transaccion_del_locatario(actor_id, transaccion_id)
        transaccion.confirmar(self._reloj(), actor_id)
        self._transacciones.guardar(transaccion)
        return transaccion

    def completar(self, actor_id: int, transaccion_id: int | None) -> Transaccion:
        transaccion = self._transaccion_del_locatario(actor_id, transaccion_id)
        transaccion.completar(self._reloj(), actor_id)
        self._transacciones.guardar(transaccion)
        return transaccion

    # -- Ambos ----------------------------------------------------------- #

    def cancelar(self, actor_id: int, transaccion_id: int | None, motivo: str = "") -> Transaccion:
        actor = obtener_usuario_activo(self._usuarios, actor_id)
        transaccion = self._obtener(transaccion_id)
        if actor.rol is Rol.CLIENTE:
            if transaccion.usuario_id != actor.id:
                raise OperacionNoAutorizada("Solo puedes cancelar tus propias transacciones.")
        else:
            restaurante = obtener_restaurante(self._restaurantes, transaccion.restaurante_id)
            exigir_propietario(actor, restaurante)
        transaccion.cancelar(self._reloj(), actor.id, motivo)
        self._transacciones.guardar(transaccion)
        return transaccion

    # -- Auxiliares ------------------------------------------------------ #

    def _obtener(self, transaccion_id: int | None) -> Transaccion:
        transaccion = (
            self._transacciones.obtener(int(transaccion_id)) if transaccion_id is not None else None
        )
        if transaccion is None:
            raise EntidadNoEncontrada("Selecciona una transacción válida.")
        return transaccion

    def _transaccion_del_locatario(self, actor_id: int, transaccion_id: int | None) -> Transaccion:
        actor = obtener_usuario_activo(self._usuarios, actor_id)
        transaccion = self._obtener(transaccion_id)
        restaurante = obtener_restaurante(self._restaurantes, transaccion.restaurante_id)
        exigir_propietario(actor, restaurante, permitir_admin=False)
        return transaccion
