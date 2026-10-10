"""Entidades del dominio (sección 6 del Documento Fundamental).

Principios aplicados:

- **Information Expert (GRASP):** ``Transaccion.puede_evaluarse()`` vive en la
  transacción porque es ella quien conoce su estado y si ya fue evaluada.
- **Encapsulamiento:** el estado de la transacción es privado; solo cambia
  mediante operaciones con significado de negocio (``confirmar``,
  ``completar``, ``cancelar``...). La interfaz nunca asigna el estado (CA-08).
- **Alta cohesión:** cada clase conoce y hace únicamente lo que le corresponde.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation

from .estados import (
    TRANSICIONES_TRANSACCION,
    EstadoEvaluacion,
    EstadoRestaurante,
    EstadoTransaccion,
    EstadoUsuario,
    Rol,
)
from .excepciones import (
    DatosInvalidos,
    EvaluacionNoPermitida,
    MotivoRechazo,
    TransicionInvalida,
)

# --------------------------------------------------------------------------- #
# Constantes de negocio
# --------------------------------------------------------------------------- #

CALIFICACION_MINIMA = 1
CALIFICACION_MAXIMA = 5
LONGITUD_MINIMA_COMENTARIO = 10
LONGITUD_MAXIMA_COMENTARIO = 500

DIAS_SEMANA = ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")

#: Formas de pago que el restaurante acepta **en el local** (RN-07).
#: ¿Qué Como? no procesa ni ofrece pagos en línea (transferencias, pasarelas,
#: carteras digitales): solo informa cómo se puede pagar al consumir.
FORMAS_PAGO_PERMITIDAS: tuple[str, ...] = ("Efectivo", "Tarjeta de débito", "Tarjeta de crédito")

RADIO_TIERRA_KM = 6371.0


def a_decimal(valor: object, campo: str) -> Decimal:
    """Convierte un valor a ``Decimal`` positivo con dos decimales."""
    try:
        numero = Decimal(str(valor)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise DatosInvalidos(f"El campo «{campo}» debe ser un número.") from exc
    if not numero.is_finite() or numero <= 0:
        raise DatosInvalidos(f"El campo «{campo}» debe ser mayor que cero.")
    return numero


def _texto_obligatorio(valor: str | None, campo: str, maximo: int = 200) -> str:
    texto = (valor or "").strip()
    if not texto:
        raise DatosInvalidos(f"El campo «{campo}» es obligatorio.")
    if len(texto) > maximo:
        raise DatosInvalidos(f"El campo «{campo}» admite como máximo {maximo} caracteres.")
    return texto


# --------------------------------------------------------------------------- #
# Objetos de valor
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Ubicacion:
    """Ubicación de un restaurante (1 Restaurante → 1 Ubicación)."""

    direccion: str
    latitud: float
    longitud: float
    zona: str = ""

    def __post_init__(self) -> None:
        if not -90 <= self.latitud <= 90 or not -180 <= self.longitud <= 180:
            raise DatosInvalidos("Las coordenadas de la ubicación no son válidas.")

    def distancia_km(self, latitud: float, longitud: float) -> float:
        """Distancia en línea recta (fórmula de Haversine)."""
        lat1, lon1 = math.radians(self.latitud), math.radians(self.longitud)
        lat2, lon2 = math.radians(latitud), math.radians(longitud)
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return 2 * RADIO_TIERRA_KM * math.asin(math.sqrt(a))


@dataclass(frozen=True)
class Horario:
    """Horario semanal. ``dias`` usa 0 = lunes … 6 = domingo.

    Si ``cierre`` es menor o igual que ``apertura``, el horario cruza la
    medianoche (por ejemplo, de 18:00 a 02:00).
    """

    dias: frozenset[int]
    apertura: time
    cierre: time

    def __post_init__(self) -> None:
        if not self.dias or not all(0 <= d <= 6 for d in self.dias):
            raise DatosInvalidos("El horario debe incluir al menos un día válido.")

    @property
    def cruza_medianoche(self) -> bool:
        return self.cierre <= self.apertura

    def esta_abierto(self, momento: datetime) -> bool:
        hora, dia = momento.time(), momento.weekday()
        if not self.cruza_medianoche:
            return dia in self.dias and self.apertura <= hora < self.cierre
        # Tramo de la noche (día de apertura) o madrugada (día siguiente).
        if dia in self.dias and hora >= self.apertura:
            return True
        dia_anterior = (momento - timedelta(days=1)).weekday()
        return dia_anterior in self.dias and hora < self.cierre

    def describir(self) -> str:
        dias = sorted(self.dias)
        if dias == list(range(7)):
            texto_dias = "Todos los días"
        elif dias == list(range(dias[0], dias[-1] + 1)) and len(dias) > 2:
            texto_dias = f"{DIAS_SEMANA[dias[0]]} a {DIAS_SEMANA[dias[-1]]}"
        else:
            texto_dias = ", ".join(DIAS_SEMANA[d] for d in dias)
        return f"{texto_dias}, {self.apertura:%H:%M}–{self.cierre:%H:%M}"


# --------------------------------------------------------------------------- #
# Oferta del restaurante: Menú, Producto, Promoción
# --------------------------------------------------------------------------- #


@dataclass
class Producto:
    id: int
    nombre: str
    precio: Decimal
    descripcion: str = ""
    disponible: bool = True

    def __post_init__(self) -> None:
        self.nombre = _texto_obligatorio(self.nombre, "nombre del producto", 120)
        self.precio = a_decimal(self.precio, "precio")


@dataclass
class Menu:
    """Agrupa la oferta gastronómica (1 Menú → 1..* Productos)."""

    id: int
    nombre: str
    descripcion: str = ""
    productos: list[Producto] = field(default_factory=list)
    activo: bool = True

    def agregar_producto(self, producto: Producto) -> None:
        if any(p.nombre.lower() == producto.nombre.lower() for p in self.productos):
            raise DatosInvalidos(f"Ya existe un producto llamado «{producto.nombre}».")
        self.productos.append(producto)

    def productos_disponibles(self) -> list[Producto]:
        return [p for p in self.productos if p.disponible]


@dataclass
class Promocion:
    id: int
    descripcion: str
    inicio: date
    fin: date
    condiciones: str = ""

    def __post_init__(self) -> None:
        self.descripcion = _texto_obligatorio(self.descripcion, "descripción de la promoción")
        if self.fin < self.inicio:
            raise DatosInvalidos("La vigencia de la promoción termina antes de comenzar.")

    def esta_vigente(self, hoy: date) -> bool:
        return self.inicio <= hoy <= self.fin


# --------------------------------------------------------------------------- #
# Actores: Usuario y Restaurante
# --------------------------------------------------------------------------- #


@dataclass
class Usuario:
    id: int
    nombre: str
    contacto: str
    rol: Rol = Rol.CLIENTE
    estado: EstadoUsuario = EstadoUsuario.ACTIVO

    @property
    def esta_activo(self) -> bool:
        return self.estado is EstadoUsuario.ACTIVO

    def nombre_publico(self) -> str:
        """Nombre mostrado junto a sus evaluaciones (minimización de datos).

        Solo se publica el primer nombre y la inicial del apellido.
        """
        partes = self.nombre.split()
        if len(partes) == 1:
            return partes[0]
        return f"{partes[0]} {partes[1][0]}."


@dataclass
class Restaurante:
    id: int
    nombre: str
    descripcion: str
    categoria: str
    ubicacion: Ubicacion
    horario: Horario
    formas_pago: frozenset[str]
    precio_promedio: Decimal
    fecha_apertura: date
    locatario_id: int
    estado: EstadoRestaurante = EstadoRestaurante.ACTIVO
    menus: list[Menu] = field(default_factory=list)
    promociones: list[Promocion] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.nombre = _texto_obligatorio(self.nombre, "nombre del restaurante", 120)
        self.categoria = _texto_obligatorio(self.categoria, "tipo de comida", 60)
        self.precio_promedio = a_decimal(self.precio_promedio, "precio promedio")
        if not self.formas_pago:
            raise DatosInvalidos("Indica al menos una forma de pago.")
        no_permitidas = set(self.formas_pago) - set(FORMAS_PAGO_PERMITIDAS)
        if no_permitidas:
            raise DatosInvalidos(
                f"Forma de pago no permitida: {', '.join(sorted(no_permitidas))}. "
                "¿Qué Como? no maneja pagos en línea; solo se registran pagos en el local "
                f"({', '.join(FORMAS_PAGO_PERMITIDAS)})."
            )

    # -- Conocer --------------------------------------------------------- #

    def esta_disponible(self) -> bool:
        return self.estado is EstadoRestaurante.ACTIVO

    def antiguedad_anios(self, hoy: date) -> int:
        anios = hoy.year - self.fecha_apertura.year
        if (hoy.month, hoy.day) < (self.fecha_apertura.month, self.fecha_apertura.day):
            anios -= 1
        return max(anios, 0)

    def promociones_vigentes(self, hoy: date) -> list[Promocion]:
        return [p for p in self.promociones if p.esta_vigente(hoy)]

    def productos(self) -> list[Producto]:
        return [p for m in self.menus if m.activo for p in m.productos_disponibles()]

    def acepta_pago(self, forma_pago: str) -> bool:
        return forma_pago in self.formas_pago

    # -- Hacer ----------------------------------------------------------- #

    def recibir_evaluacion(self, evaluacion: Evaluacion) -> None:
        """Verifica que la evaluación corresponda a este restaurante y que
        el restaurante pueda recibirla (extensión «Restaurante no disponible»).
        """
        if evaluacion.restaurante_id != self.id:
            raise DatosInvalidos("La evaluación no corresponde a este restaurante.")
        if not self.esta_disponible():
            raise EvaluacionNoPermitida(
                MotivoRechazo.RESTAURANTE_NO_DISPONIBLE,
                f"«{self.nombre}» no está disponible en este momento.",
            )

    def menu_principal(self) -> Menu:
        if not self.menus:
            self.menus.append(Menu(id=1, nombre="Menú principal"))
        return self.menus[0]


# --------------------------------------------------------------------------- #
# Transacción: el corazón de la regla de confianza
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class CambioEstado:
    """Registro inmutable de cada transición (trazabilidad / auditoría)."""

    estado: EstadoTransaccion
    fecha: datetime
    actor_id: int | None
    nota: str = ""


class Transaccion:
    """Relación comercial entre un usuario y un restaurante.

    El estado es privado. Solo cambia mediante ``enviar``, ``confirmar``,
    ``completar`` y ``cancelar``, que validan la máquina de estados.
    """

    def __init__(
        self,
        id: int,
        usuario_id: int,
        restaurante_id: int,
        importe: Decimal | float | str,
        fecha: datetime,
        actor_id: int | None = None,
    ) -> None:
        self._id = id
        self._usuario_id = usuario_id
        self._restaurante_id = restaurante_id
        self._importe = a_decimal(importe, "importe")
        self._fecha = fecha
        self._estado = EstadoTransaccion.INICIADA
        self._evaluacion_id: int | None = None
        self._historial: list[CambioEstado] = [
            CambioEstado(EstadoTransaccion.INICIADA, fecha, actor_id, "Transacción registrada")
        ]

    # -- Propiedades de solo lectura ------------------------------------- #

    @property
    def id(self) -> int:
        return self._id

    @property
    def usuario_id(self) -> int:
        return self._usuario_id

    @property
    def restaurante_id(self) -> int:
        return self._restaurante_id

    @property
    def importe(self) -> Decimal:
        return self._importe

    @property
    def fecha(self) -> datetime:
        return self._fecha

    @property
    def estado(self) -> EstadoTransaccion:
        return self._estado

    @property
    def evaluacion_id(self) -> int | None:
        return self._evaluacion_id

    @property
    def historial(self) -> tuple[CambioEstado, ...]:
        return tuple(self._historial)

    # -- Máquina de estados ---------------------------------------------- #

    def _transicionar(
        self, destino: EstadoTransaccion, momento: datetime, actor_id: int | None, nota: str
    ) -> None:
        if destino not in TRANSICIONES_TRANSACCION[self._estado]:
            raise TransicionInvalida(
                f"La transacción #{self._id} no puede pasar de "
                f"{self._estado.value} a {destino.value}."
            )
        self._estado = destino
        self._historial.append(CambioEstado(destino, momento, actor_id, nota))

    def enviar(self, momento: datetime, actor_id: int | None = None) -> None:
        """INICIADA → PENDIENTE: queda en espera de confirmación del restaurante."""
        self._transicionar(EstadoTransaccion.PENDIENTE, momento, actor_id, "Enviada al restaurante")

    def confirmar(self, momento: datetime, actor_id: int | None = None) -> None:
        """PENDIENTE → CONFIRMADA."""
        self._transicionar(EstadoTransaccion.CONFIRMADA, momento, actor_id, "Confirmada")

    def completar(self, momento: datetime, actor_id: int | None = None) -> None:
        """CONFIRMADA → COMPLETADA: la relación comercial concluyó."""
        self._transicionar(EstadoTransaccion.COMPLETADA, momento, actor_id, "Completada")

    def cancelar(self, momento: datetime, actor_id: int | None = None, motivo: str = "") -> None:
        """PENDIENTE o CONFIRMADA → CANCELADA."""
        self._transicionar(
            EstadoTransaccion.CANCELADA, momento, actor_id, motivo or "Cancelada"
        )

    # -- Information Expert: ¿puede respaldar una evaluación? ------------ #

    def es_valida(self) -> bool:
        """Una transacción es válida como evidencia si está COMPLETADA (RN-05)."""
        return self._estado is EstadoTransaccion.COMPLETADA

    def puede_evaluarse(self) -> bool:
        """Guarda principal (sección 10.4):

        ``[estado == COMPLETADA AND noExisteEvaluacion] → true``
        """
        return self.es_valida() and self._evaluacion_id is None

    def verificar_evaluable_por(self, usuario_id: int) -> None:
        """Igual que ``puede_evaluarse`` pero explica el motivo del rechazo."""
        if self._usuario_id != usuario_id:
            raise EvaluacionNoPermitida(
                MotivoRechazo.TRANSACCION_AJENA,
                "Solo la persona que realizó la transacción puede evaluarla.",
            )
        if self._estado is EstadoTransaccion.CANCELADA:
            raise EvaluacionNoPermitida(
                MotivoRechazo.TRANSACCION_CANCELADA,
                f"La transacción #{self._id} fue cancelada y no habilita una evaluación.",
            )
        if not self.es_valida():
            raise EvaluacionNoPermitida(
                MotivoRechazo.TRANSACCION_NO_COMPLETADA,
                f"La transacción #{self._id} está {self._estado.value}. "
                "Solo una transacción COMPLETADA habilita la evaluación.",
            )
        if self._evaluacion_id is not None:
            raise EvaluacionNoPermitida(
                MotivoRechazo.TRANSACCION_YA_EVALUADA,
                f"La transacción #{self._id} ya respalda una evaluación.",
            )

    def vincular_evaluacion(self, evaluacion_id: int) -> None:
        """Marca la transacción como utilizada (RN-06). Solo una vez."""
        if not self.puede_evaluarse():
            raise EvaluacionNoPermitida(
                MotivoRechazo.TRANSACCION_YA_EVALUADA,
                f"La transacción #{self._id} no puede respaldar otra evaluación.",
            )
        self._evaluacion_id = evaluacion_id

    def __repr__(self) -> str:
        return (
            f"Transaccion(id={self._id}, usuario={self._usuario_id}, "
            f"restaurante={self._restaurante_id}, estado={self._estado.value})"
        )


# --------------------------------------------------------------------------- #
# Evaluación
# --------------------------------------------------------------------------- #


@dataclass
class Evaluacion:
    """Retroalimentación vinculada a una transacción (1 Transacción → 0..1 Evaluación).

    No existe un constructor «suelto» en el flujo de negocio: se crea con
    ``Evaluacion.crear(...)`` a partir de una transacción que ya fue validada.
    Así se cumple RN-04: la evaluación nunca origina ni justifica una
    transacción, siempre es al revés.
    """

    id: int
    usuario_id: int
    restaurante_id: int
    transaccion_id: int
    calificacion: int
    comentario: str
    fecha: datetime
    estado: EstadoEvaluacion = EstadoEvaluacion.PUBLICADA
    motivo_moderacion: str = ""

    @classmethod
    def crear(
        cls,
        id: int,
        transaccion: Transaccion,
        calificacion: int | float | str | None,
        comentario: str | None,
        fecha: datetime,
    ) -> Evaluacion:
        if not transaccion.puede_evaluarse():
            raise EvaluacionNoPermitida(
                MotivoRechazo.SIN_TRANSACCION,
                "Se requiere una transacción válida para registrar la evaluación.",
            )
        evaluacion = cls(
            id=id,
            usuario_id=transaccion.usuario_id,
            restaurante_id=transaccion.restaurante_id,
            transaccion_id=transaccion.id,
            calificacion=cls._normalizar_calificacion(calificacion),
            comentario=(comentario or "").strip(),
            fecha=fecha,
        )
        evaluacion.validar()
        return evaluacion

    @staticmethod
    def _normalizar_calificacion(valor: int | float | str | None) -> int:
        if valor is None or valor == "":
            raise DatosInvalidos("Selecciona una calificación.")
        try:
            numero = float(valor)
        except (TypeError, ValueError) as exc:
            raise DatosInvalidos("La calificación debe ser un número entero.") from exc
        if not numero.is_integer():
            raise DatosInvalidos("La calificación debe ser un número entero.")
        return int(numero)

    def validar(self) -> None:
        """Extensión «Evaluación incompleta»: exige los datos obligatorios."""
        if not CALIFICACION_MINIMA <= self.calificacion <= CALIFICACION_MAXIMA:
            raise DatosInvalidos(
                f"La calificación debe estar entre {CALIFICACION_MINIMA} y {CALIFICACION_MAXIMA}."
            )
        if len(self.comentario) < LONGITUD_MINIMA_COMENTARIO:
            raise DatosInvalidos(
                f"El comentario debe tener al menos {LONGITUD_MINIMA_COMENTARIO} caracteres."
            )
        if len(self.comentario) > LONGITUD_MAXIMA_COMENTARIO:
            raise DatosInvalidos(
                f"El comentario admite como máximo {LONGITUD_MAXIMA_COMENTARIO} caracteres."
            )

    @property
    def esta_publicada(self) -> bool:
        return self.estado is EstadoEvaluacion.PUBLICADA

    def ocultar(self, motivo: str) -> None:
        """Moderación: la evaluación deja de contar para el ranking."""
        self.motivo_moderacion = _texto_obligatorio(motivo, "motivo de moderación", 300)
        self.estado = EstadoEvaluacion.OCULTA

    def restaurar(self) -> None:
        self.estado = EstadoEvaluacion.PUBLICADA
        self.motivo_moderacion = ""
