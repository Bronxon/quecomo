"""Reglas de autorización por rol.

Centralizar estas comprobaciones evita que cada pantalla decida por su
cuenta quién puede hacer qué (requisito de Seguridad, sección 4.2).

Nota: en el MVP el «inicio de sesión» es simulado (se elige un usuario de
demostración). Estas funciones son las que seguirán aplicando cuando se
integre una autenticación real.
"""

from __future__ import annotations

from ..dominio.entidades import Restaurante, Usuario
from ..dominio.estados import Rol
from ..dominio.excepciones import EntidadNoEncontrada, OperacionNoAutorizada
from ..dominio.repositorios import IRepositorioRestaurantes, IRepositorioUsuarios


def obtener_usuario_activo(usuarios: IRepositorioUsuarios, usuario_id: int | None) -> Usuario:
    usuario = usuarios.obtener(int(usuario_id)) if usuario_id is not None else None
    if usuario is None:
        raise OperacionNoAutorizada("Selecciona un usuario para continuar.")
    if not usuario.esta_activo:
        raise OperacionNoAutorizada("La cuenta seleccionada no está activa.")
    return usuario


def exigir_rol(usuario: Usuario, *roles: Rol) -> None:
    if usuario.rol not in roles:
        permitidos = " o ".join(r.etiqueta for r in roles)
        raise OperacionNoAutorizada(f"Esta operación es exclusiva del rol {permitidos}.")


def obtener_restaurante(
    restaurantes: IRepositorioRestaurantes, restaurante_id: int | None
) -> Restaurante:
    restaurante = (
        restaurantes.obtener(int(restaurante_id)) if restaurante_id is not None else None
    )
    if restaurante is None:
        raise EntidadNoEncontrada("Selecciona un restaurante válido.")
    return restaurante


def exigir_propietario(
    usuario: Usuario, restaurante: Restaurante, permitir_admin: bool = True
) -> None:
    """Solo el locatario dueño del restaurante (o un administrador) lo gestiona.

    Con ``permitir_admin=False`` ni siquiera un administrador puede actuar:
    se usa para confirmar o completar transacciones, de modo que nadie ajeno
    a la relación comercial pueda fabricar la evidencia de una evaluación.
    """
    if permitir_admin and usuario.rol is Rol.ADMINISTRADOR:
        return
    if usuario.rol is not Rol.LOCATARIO or restaurante.locatario_id != usuario.id:
        raise OperacionNoAutorizada(
            f"Solo el locatario de «{restaurante.nombre}» puede realizar esta operación."
        )
