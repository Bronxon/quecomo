"""Administración de restaurantes y moderación (HU-09, HU-10, HU-11 y rol
Administrador de la sección 2.1)."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date, datetime, time

from ..dominio.entidades import (
    Evaluacion,
    Horario,
    Menu,
    Producto,
    Promocion,
    Restaurante,
    Ubicacion,
    a_decimal,
)
from ..dominio.estados import EstadoRestaurante, Rol
from ..dominio.excepciones import DatosInvalidos, EntidadNoEncontrada
from ..dominio.repositorios import (
    IRepositorioEvaluaciones,
    IRepositorioRestaurantes,
    IRepositorioUsuarios,
)
from .autorizacion import (
    exigir_propietario,
    exigir_rol,
    obtener_restaurante,
    obtener_usuario_activo,
)


def leer_hora(texto: str | None, campo: str) -> time:
    try:
        return datetime.strptime((texto or "").strip(), "%H:%M").time()
    except ValueError as exc:
        raise DatosInvalidos(f"«{campo}» debe tener el formato HH:MM (por ejemplo, 13:30).") from exc


def leer_fecha(texto: str | date | None, campo: str) -> date:
    if isinstance(texto, date):
        return texto
    try:
        return datetime.strptime((texto or "").strip(), "%Y-%m-%d").date()
    except ValueError as exc:
        raise DatosInvalidos(f"«{campo}» debe tener el formato AAAA-MM-DD.") from exc


@dataclass
class DatosRestaurante:
    """Datos capturados en el formulario del locatario."""

    nombre: str
    descripcion: str
    categoria: str
    direccion: str
    latitud: float
    longitud: float
    zona: str
    dias: Iterable[int]
    apertura: str
    cierre: str
    formas_pago: Iterable[str]
    precio_promedio: object
    fecha_apertura: str | date


class ServicioRestaurantes:
    def __init__(
        self,
        usuarios: IRepositorioUsuarios,
        restaurantes: IRepositorioRestaurantes,
        evaluaciones: IRepositorioEvaluaciones,
        reloj: Callable[[], datetime] = datetime.now,
    ) -> None:
        self._usuarios = usuarios
        self._restaurantes = restaurantes
        self._evaluaciones = evaluaciones
        self._reloj = reloj

    # -- Locatario -------------------------------------------------------- #

    def mis_restaurantes(self, actor_id: int) -> list[Restaurante]:
        actor = obtener_usuario_activo(self._usuarios, actor_id)
        if actor.rol is Rol.ADMINISTRADOR:
            return self._restaurantes.listar()
        exigir_rol(actor, Rol.LOCATARIO)
        return self._restaurantes.listar_por_locatario(actor.id)

    def registrar(self, actor_id: int, datos: DatosRestaurante) -> Restaurante:
        """HU-09: el locatario registra su restaurante."""
        actor = obtener_usuario_activo(self._usuarios, actor_id)
        exigir_rol(actor, Rol.LOCATARIO)
        restaurante = Restaurante(
            id=self._restaurantes.siguiente_id(),
            locatario_id=actor.id,
            menus=[Menu(id=1, nombre="Menú principal")],
            **self._campos(datos),
        )
        self._restaurantes.guardar(restaurante)
        return restaurante

    def actualizar(self, actor_id: int, restaurante_id: int | None, datos: DatosRestaurante) -> Restaurante:
        """HU-10: el locatario mantiene su información actualizada."""
        actor = obtener_usuario_activo(self._usuarios, actor_id)
        actual = obtener_restaurante(self._restaurantes, restaurante_id)
        exigir_propietario(actor, actual)
        # Se construye un objeto nuevo para que las validaciones de la
        # entidad se apliquen completas; si fallan, el original no cambia.
        nuevo = Restaurante(
            id=actual.id,
            locatario_id=actual.locatario_id,
            estado=actual.estado,
            menus=actual.menus,
            promociones=actual.promociones,
            **self._campos(datos),
        )
        self._restaurantes.guardar(nuevo)
        return nuevo

    def agregar_producto(
        self, actor_id: int, restaurante_id: int | None, nombre: str, precio: object, descripcion: str = ""
    ) -> Producto:
        restaurante = self._propio(actor_id, restaurante_id)
        menu = restaurante.menu_principal()
        producto = Producto(
            id=max((p.id for p in menu.productos), default=0) + 1,
            nombre=nombre,
            precio=precio,
            descripcion=(descripcion or "").strip(),
        )
        menu.agregar_producto(producto)
        self._restaurantes.guardar(restaurante)
        return producto

    def agregar_promocion(
        self,
        actor_id: int,
        restaurante_id: int | None,
        descripcion: str,
        inicio: str | date,
        fin: str | date,
        condiciones: str = "",
    ) -> Promocion:
        restaurante = self._propio(actor_id, restaurante_id)
        promocion = Promocion(
            id=max((p.id for p in restaurante.promociones), default=0) + 1,
            descripcion=descripcion,
            inicio=leer_fecha(inicio, "Inicio"),
            fin=leer_fecha(fin, "Fin"),
            condiciones=(condiciones or "").strip(),
        )
        restaurante.promociones.append(promocion)
        self._restaurantes.guardar(restaurante)
        return promocion

    def evaluaciones_recibidas(self, actor_id: int, restaurante_id: int | None) -> list[Evaluacion]:
        """HU-11: el locatario consulta sus evaluaciones (incluye moderadas)."""
        restaurante = self._propio(actor_id, restaurante_id)
        return sorted(
            self._evaluaciones.obtener_por_restaurante(restaurante.id, incluir_ocultas=True),
            key=lambda e: e.fecha,
            reverse=True,
        )

    # -- Administrador ---------------------------------------------------- #

    def cambiar_estado(
        self, admin_id: int, restaurante_id: int | None, estado: EstadoRestaurante
    ) -> Restaurante:
        admin = obtener_usuario_activo(self._usuarios, admin_id)
        exigir_rol(admin, Rol.ADMINISTRADOR)
        restaurante = obtener_restaurante(self._restaurantes, restaurante_id)
        restaurante.estado = estado
        self._restaurantes.guardar(restaurante)
        return restaurante

    def todas_las_evaluaciones(self, admin_id: int) -> list[Evaluacion]:
        admin = obtener_usuario_activo(self._usuarios, admin_id)
        exigir_rol(admin, Rol.ADMINISTRADOR)
        return sorted(self._evaluaciones.listar(), key=lambda e: e.id, reverse=True)

    def ocultar_evaluacion(self, admin_id: int, evaluacion_id: int | None, motivo: str) -> Evaluacion:
        evaluacion = self._evaluacion_para_moderar(admin_id, evaluacion_id)
        evaluacion.ocultar(motivo)
        self._evaluaciones.guardar(evaluacion)
        return evaluacion

    def restaurar_evaluacion(self, admin_id: int, evaluacion_id: int | None) -> Evaluacion:
        evaluacion = self._evaluacion_para_moderar(admin_id, evaluacion_id)
        evaluacion.restaurar()
        self._evaluaciones.guardar(evaluacion)
        return evaluacion

    # -- Auxiliares ------------------------------------------------------- #

    def _propio(self, actor_id: int, restaurante_id: int | None) -> Restaurante:
        actor = obtener_usuario_activo(self._usuarios, actor_id)
        restaurante = obtener_restaurante(self._restaurantes, restaurante_id)
        exigir_propietario(actor, restaurante)
        return restaurante

    def _evaluacion_para_moderar(self, admin_id: int, evaluacion_id: int | None) -> Evaluacion:
        admin = obtener_usuario_activo(self._usuarios, admin_id)
        exigir_rol(admin, Rol.ADMINISTRADOR)
        evaluacion = (
            self._evaluaciones.obtener(int(evaluacion_id)) if evaluacion_id is not None else None
        )
        if evaluacion is None:
            raise EntidadNoEncontrada("Selecciona una evaluación válida.")
        return evaluacion

    @staticmethod
    def _campos(datos: DatosRestaurante) -> dict:
        try:
            latitud, longitud = float(datos.latitud), float(datos.longitud)
        except (TypeError, ValueError) as exc:
            raise DatosInvalidos("Latitud y longitud deben ser números.") from exc
        return {
            "nombre": datos.nombre,
            "descripcion": (datos.descripcion or "").strip(),
            "categoria": datos.categoria,
            "ubicacion": Ubicacion(
                direccion=(datos.direccion or "").strip() or "Sin dirección",
                latitud=latitud,
                longitud=longitud,
                zona=(datos.zona or "").strip(),
            ),
            "horario": Horario(
                dias=frozenset(int(d) for d in datos.dias),
                apertura=leer_hora(datos.apertura, "Apertura"),
                cierre=leer_hora(datos.cierre, "Cierre"),
            ),
            "formas_pago": frozenset(datos.formas_pago or []),
            "precio_promedio": a_decimal(datos.precio_promedio, "precio promedio"),
            "fecha_apertura": leer_fecha(datos.fecha_apertura, "Fecha de apertura"),
        }
