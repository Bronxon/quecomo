"""Adaptador entre la interfaz Gradio y la capa de aplicación.

Cada método recibe valores simples de los componentes (texto, números, ids)
y devuelve datos listos para mostrar (tablas, Markdown, opciones). Aquí **no**
se decide ninguna regla de negocio: si una operación no procede, el servicio
lanza un ``ErrorDominio`` y aquí solo se traduce a un mensaje.

Separar esta clase de ``interfaz.py`` permite probar la presentación sin
levantar un servidor web.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from functools import wraps
from typing import Any

import pandas as pd

from ..aplicacion.servicio_busqueda import CriteriosBusqueda, Orden, ResultadoBusqueda
from ..aplicacion.servicio_restaurantes import DatosRestaurante
from ..configuracion import Aplicacion
from ..dominio.entidades import DIAS_SEMANA, Restaurante, Transaccion
from ..dominio.estados import EstadoRestaurante, EstadoTransaccion, Rol
from ..dominio.excepciones import DatosInvalidos, ErrorDominio, EvaluacionNoPermitida, MotivoRechazo

HORARIO_CUALQUIERA = "Cualquier horario"
HORARIO_AHORA = "Abierto ahora"
OPCIONES_HORARIO = [HORARIO_CUALQUIERA, HORARIO_AHORA] + [f"{h:02d}:00" for h in range(7, 24)]
TODAS = "Todas"
SIN_REFERENCIA = "Sin punto de referencia"

ICONOS_ESTADO = {
    EstadoTransaccion.INICIADA: "⚪ INICIADA",
    EstadoTransaccion.PENDIENTE: "🟡 PENDIENTE",
    EstadoTransaccion.CONFIRMADA: "🔵 CONFIRMADA",
    EstadoTransaccion.COMPLETADA: "🟢 COMPLETADA",
    EstadoTransaccion.CANCELADA: "🔴 CANCELADA",
}


# --------------------------------------------------------------------------- #
# Formato
# --------------------------------------------------------------------------- #


def dinero(valor: Decimal | float) -> str:
    return f"${valor:,.2f}"


def fecha_hora(valor: datetime) -> str:
    return valor.strftime("%d/%m/%Y %H:%M")


def estrellas(calificacion: float | None) -> str:
    if calificacion is None:
        return "—"
    llenas = int(calificacion + 0.5)  # redondeo convencional (4.5 → 5)
    return "★" * llenas + "☆" * (5 - llenas)


def ok(texto: str) -> str:
    return f"✅ {texto}"


def aviso(texto: str) -> str:
    return f"⛔ {texto}"


def capturar_errores(*salidas_por_defecto: Any) -> Callable:
    """Convierte un ``ErrorDominio`` en mensaje para la persona usuaria.

    El mensaje va en la primera salida; las demás reciben los valores por
    defecto indicados (normalmente ``gr.update()``, «no cambiar»).
    """

    def decorador(funcion: Callable) -> Callable:
        @wraps(funcion)
        def envoltura(*args: Any, **kwargs: Any) -> Any:
            try:
                return funcion(*args, **kwargs)
            except ErrorDominio as error:
                if not salidas_por_defecto:
                    return aviso(str(error))
                return (aviso(str(error)), *salidas_por_defecto)

        return envoltura

    return decorador


def _id(valor: Any) -> int | None:
    if valor in (None, "", []):
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


class Vista:
    def __init__(self, app: Aplicacion) -> None:
        self.app = app

    # ------------------------------------------------------------------ #
    # Sesión (inicio de sesión simulado)
    # ------------------------------------------------------------------ #

    def opciones_usuarios(self) -> list[tuple[str, int]]:
        return [(f"{u.nombre} · {u.rol.etiqueta}", u.id) for u in self.app.usuarios.listar()]

    def rol_de(self, usuario_id: Any) -> Rol | None:
        usuario = self.app.usuarios.obtener(_id(usuario_id) or -1)
        return usuario.rol if usuario else None

    def bienvenida(self, usuario_id: Any) -> str:
        usuario = self.app.usuarios.obtener(_id(usuario_id) or -1)
        if usuario is None:
            return "Selecciona un usuario de demostración."
        consejos = {
            Rol.CLIENTE: "Busca y compara restaurantes; registra y evalúa tus consumos en **Evaluar**.",
            Rol.LOCATARIO: "Gestiona tus restaurantes y confirma consumos en **Locatario**.",
            Rol.ADMINISTRADOR: "Modera evaluaciones y restaurantes en **Administración**.",
        }
        return f"Hola, **{usuario.nombre.split()[0]}** ({usuario.rol.etiqueta.lower()}). {consejos[usuario.rol]}"

    # ------------------------------------------------------------------ #
    # Catálogos
    # ------------------------------------------------------------------ #

    def opciones_categorias(self) -> list[str]:
        return [TODAS, *self.app.busqueda.categorias()]

    def opciones_formas_pago(self) -> list[str]:
        return [TODAS, *self.app.busqueda.formas_pago()]

    def opciones_puntos(self) -> list[str]:
        return [SIN_REFERENCIA, *(p.nombre for p in self.app.puntos_referencia)]

    def opciones_restaurantes(self) -> list[tuple[str, int]]:
        return [(r.nombre, r.id) for r in self.app.busqueda.restaurantes_disponibles()]

    # ------------------------------------------------------------------ #
    # Buscar (HU-01, HU-02, HU-05)
    # ------------------------------------------------------------------ #

    def _momento(self, horario: str | None) -> datetime | None:
        if not horario or horario == HORARIO_CUALQUIERA:
            return None
        ahora = self.app.reloj()
        if horario == HORARIO_AHORA:
            return ahora
        momento = datetime.combine(ahora.date(), time.fromisoformat(horario))
        # Si esa hora ya pasó hoy, se interpreta como la de mañana.
        if momento.hour < ahora.hour:
            momento += timedelta(days=1)
        return momento

    
    def buscar(
        self,
        texto: str,
        categoria: str,
        precio_maximo: float,
        punto: str,
        distancia_maxima: float,
        horario: str,
        forma_pago: str,
        calificacion_minima: float,
        solo_promocion: bool,
        orden: str,
    ) -> tuple[pd.DataFrame, str]:
        referencia = self.app.punto(punto)
        criterios = self._crear_criterios_busqueda(
            texto,
            categoria,
            precio_maximo,
            referencia,
            distancia_maxima,
            horario,
            forma_pago,
            calificacion_minima,
            solo_promocion,
            orden,
        )
        resultados = self.app.busqueda.buscar(criterios)
        tabla = pd.DataFrame(
            [self._fila_resultado(r) for r in resultados],
            columns=[
                "ID",
                "Restaurante",
                "Tipo",
                "Precio prom.",
                "km",
                "Calificación",
                "Eval.",
                "Abierto",
                "Promo",
            ],
        )
        if not resultados:
            return tabla, "No hay restaurantes que cumplan todos los criterios. Prueba a relajar algún filtro."
        sufijo = "" if referencia else " Elige un punto de referencia para ver distancias."
        return tabla, f"**{len(resultados)}** restaurante(s) encontrado(s).{sufijo}"

    def _crear_criterios_busqueda(
        self,
        texto: str,
        categoria: str,
        precio_maximo: float,
        referencia: Any,
        distancia_maxima: float,
        horario: str,
        forma_pago: str,
        calificacion_minima: float,
        solo_promocion: bool,
        orden: str,
    ) -> CriteriosBusqueda:
        return CriteriosBusqueda(
            texto=texto or "",
            categoria=None if categoria in (None, TODAS) else categoria,
            precio_maximo=float(precio_maximo) if precio_maximo else None,
            punto=referencia,
            distancia_maxima_km=(
                float(distancia_maxima)
                if referencia and distancia_maxima
                else None
            ),
            abierto_en=self._momento(horario),
            forma_pago=None if forma_pago in (None, TODAS) else forma_pago,
            calificacion_minima=(
                float(calificacion_minima) if calificacion_minima else None
            ),
            solo_con_promocion=bool(solo_promocion),
            orden=Orden(orden) if orden else Orden.RANKING,
        )


    @staticmethod
    def _fila_resultado(r: ResultadoBusqueda) -> list[Any]:
        return [
            r.restaurante.id,
            r.restaurante.nombre,
            r.restaurante.categoria,
            dinero(r.restaurante.precio_promedio),
            r.distancia_km if r.distancia_km is not None else "—",
            f"{estrellas(r.ranking.promedio)} {r.ranking.promedio:.1f}" if r.ranking.promedio else "Sin evaluaciones",
            r.ranking.total,
            "Sí" if r.abierto else "No",
            "Sí" if r.promociones_vigentes else "—",
        ]

    # ------------------------------------------------------------------ #
    # Ficha del restaurante (HU-03, HU-05)
    # ------------------------------------------------------------------ #

    
   
    def ficha(self, restaurante_id: Any, punto: str) -> tuple[str, pd.DataFrame]:
        rid = _id(restaurante_id)
        if rid is None:
            return "Selecciona un restaurante para ver su información.", pd.DataFrame()

        info = self.app.busqueda.detalle(rid, self.app.punto(punto))
        r = info.restaurante
        hoy = self.app.reloj().date()

        lineas = self._lineas_basicas_ficha(info, punto)
        lineas.extend(self._lineas_promociones(r, hoy))
        lineas.extend(self._lineas_distribucion(info.ranking))
        lineas.extend(self._lineas_evaluaciones(r))

        menu = pd.DataFrame(
            [[p.nombre, p.descripcion, dinero(p.precio)] for p in r.productos()],
            columns=["Producto", "Descripción", "Precio"],
        )
        return "\n".join(lineas), menu

    def _lineas_basicas_ficha(self, info: Any, punto: str) -> list[str]:
        r = info.restaurante
        return [
            f"## {r.nombre}",
            f"*{r.categoria}* · {r.descripcion}",
            "",
            f"**Calificación:** {estrellas(info.ranking.promedio)} {info.ranking.texto()}  ",
            f"**Precio promedio por persona:** {dinero(r.precio_promedio)}  ",
            f"**Horario:** {r.horario.describir()} — {'🟢 abierto ahora' if info.abierto else '⚫ cerrado ahora'}  ",
            f"**Ubicación:** {r.ubicacion.direccion}, {r.ubicacion.zona}"
            + (f" · a {info.distancia_km} km de {punto}" if info.distancia_km is not None else "")
            + "  ",
            f"**Formas de pago en el local:** {', '.join(sorted(r.formas_pago))}  ",
            f"**Antigüedad:** {info.antiguedad_anios} año(s) (desde {r.fecha_apertura:%Y})",
        ]

    @staticmethod
    def _lineas_promociones(restaurante: Any, hoy: Any) -> list[str]:
        promos = restaurante.promociones_vigentes(hoy)
        lineas = ["", "### 🏷️ Promociones vigentes"]
        lineas.extend(
            f"- **{p.descripcion}** (hasta {p.fin:%d/%m/%Y}). {p.condiciones}"
            for p in promos
        )
        return lineas if promos else lineas + ["- Sin promociones vigentes."]

    @staticmethod
    def _lineas_distribucion(ranking: Any) -> list[str]:
        lineas = ["", "### 📊 Distribución de calificaciones"]
        total = ranking.total or 1
        for n, cantidad in ranking.distribucion.items():
            barra = "█" * round(10 * cantidad / total)
            lineas.append(f"`{n}★ {barra:<10} {cantidad}`  ")
        return lineas

    def _lineas_evaluaciones(self, restaurante: Any) -> list[str]:
        lineas = ["", "### 💬 Evaluaciones verificadas"]
        evaluaciones = sorted(
            self.app.evaluaciones.obtener_por_restaurante(restaurante.id),
            key=lambda e: e.fecha,
            reverse=True,
        )
        if not evaluaciones:
            return lineas + [
                "Aún no hay evaluaciones. Solo quien completa un consumo aquí puede evaluar."
            ]

        for e in evaluaciones:
            autor = self.app.usuarios.obtener(e.usuario_id)
            nombre = autor.nombre_publico() if autor else "Usuario"
            lineas.append(
                f"- {estrellas(e.calificacion)} **{nombre}** · {e.fecha:%d/%m/%Y}  \n"
                f"  {e.comentario}  \n"
                f"  <small>✔ Respaldada por el consumo #{e.transaccion_id}</small>"
            )
        return lineas

    # ------------------------------------------------------------------ #
    # Comparar (HU-04)
    # ------------------------------------------------------------------ #

    @capturar_errores(pd.DataFrame())
    def comparar(self, restaurante_ids: list[Any], punto: str) -> tuple[str, pd.DataFrame]:
        ids = [i for i in (_id(v) for v in (restaurante_ids or [])) if i is not None]
        resultados = self.app.busqueda.comparar(ids, self.app.punto(punto))
        hoy = self.app.reloj().date()
        criterios: dict[str, Callable[[ResultadoBusqueda], Any]] = {
            "Tipo de comida": lambda x: x.restaurante.categoria,
            "Calificación": lambda x: f"{estrellas(x.ranking.promedio)} {x.ranking.texto()}",
            "Precio promedio": lambda x: dinero(x.restaurante.precio_promedio),
            "Distancia (km)": lambda x: x.distancia_km if x.distancia_km is not None else "—",
            "Horario": lambda x: x.restaurante.horario.describir(),
            "Abierto ahora": lambda x: "Sí" if x.abierto else "No",
            "Pago en el local": lambda x: ", ".join(sorted(x.restaurante.formas_pago)),
            "Promociones vigentes": lambda x: "; ".join(p.descripcion for p in x.restaurante.promociones_vigentes(hoy)) or "—",
            "Antigüedad (años)": lambda x: x.antiguedad_anios,
            "Productos en menú": lambda x: len(x.restaurante.productos()),
            "Zona": lambda x: x.restaurante.ubicacion.zona,
        }
        filas = [[nombre, *(f(r) for r in resultados)] for nombre, f in criterios.items()]
        tabla = pd.DataFrame(filas, columns=["Criterio", *(r.restaurante.nombre for r in resultados)])
        mejor = min(resultados, key=lambda x: (x.ranking.promedio is None, -x.ranking.puntaje))
        return ok(f"Comparando {len(resultados)} restaurantes. Mejor calificado: **{mejor.restaurante.nombre}**."), tabla

    # ------------------------------------------------------------------ #
    # Registro de consumos (HU-06) — dentro de la pestaña «Evaluar»
    # ------------------------------------------------------------------ #

    def _nombre_restaurante(self, restaurante_id: int) -> str:
        r = self.app.restaurantes.obtener(restaurante_id)
        return r.nombre if r else f"#{restaurante_id}"

    def _tabla_transacciones(self, transacciones: list[Transaccion], con_cliente: bool = False) -> pd.DataFrame:
        filas = []
        for t in transacciones:
            fila = [t.id, fecha_hora(t.fecha), self._nombre_restaurante(t.restaurante_id)]
            if con_cliente:
                cliente = self.app.usuarios.obtener(t.usuario_id)
                fila.append(cliente.nombre if cliente else t.usuario_id)
            fila += [dinero(t.importe), ICONOS_ESTADO[t.estado], "Sí" if t.evaluacion_id else "No"]
            filas.append(fila)
        columnas = ["ID", "Fecha", "Restaurante"] + (["Cliente"] if con_cliente else [])
        columnas += ["Importe", "Estado", "Evaluada"]
        return pd.DataFrame(filas, columns=columnas)

    def mis_transacciones(self, usuario_id: Any) -> pd.DataFrame:
        try:
            transacciones = self.app.servicio_transacciones.listar_de_usuario(_id(usuario_id))
        except ErrorDominio:
            transacciones = []
        return self._tabla_transacciones(transacciones)

    def opciones_cancelables(self, usuario_id: Any) -> list[tuple[str, int]]:
        uid = _id(usuario_id)
        if uid is None:
            return []
        return [
            (f"#{t.id} · {self._nombre_restaurante(t.restaurante_id)} · {t.estado.value}", t.id)
            for t in self.app.transacciones.listar_por_usuario(uid)
            if t.estado in (EstadoTransaccion.PENDIENTE, EstadoTransaccion.CONFIRMADA)
        ]

    @capturar_errores()
    def registrar_transaccion(self, usuario_id: Any, restaurante_id: Any, importe: Any) -> str:
        t = self.app.servicio_transacciones.registrar(_id(usuario_id), _id(restaurante_id), importe)
        return ok(
            f"Consumo #{t.id} registrado por {dinero(t.importe)} en "
            f"«{self._nombre_restaurante(t.restaurante_id)}». Queda **PENDIENTE** hasta que el "
            "restaurante lo confirme y lo complete; entonces podrás evaluarlo."
        )

    @capturar_errores()
    def cancelar_transaccion(self, usuario_id: Any, transaccion_id: Any) -> str:
        t = self.app.servicio_transacciones.cancelar(_id(usuario_id), _id(transaccion_id), "Cancelada desde la app")
        return ok(f"Consumo #{t.id} cancelado. Un consumo cancelado no se puede evaluar.")

    # ------------------------------------------------------------------ #
    # Evaluar (CU-01: HU-07 + HU-08)
    # ------------------------------------------------------------------ #

    def opciones_para_evaluar(self, usuario_id: Any) -> list[tuple[str, int]]:
        """Todas las transacciones del usuario, marcando cuáles son evaluables.

        Se muestran también las no evaluables para que la persona pueda ver
        por qué el sistema las rechaza (extensiones de CU-01).
        """
        uid = _id(usuario_id)
        if uid is None:
            return []
        opciones = []
        for t in sorted(self.app.transacciones.listar_por_usuario(uid), key=lambda x: x.id, reverse=True):
            marca = "✔ listo para evaluar" if t.puede_evaluarse() else ("ya evaluado" if t.evaluacion_id else t.estado.value)
            opciones.append((f"#{t.id} · {self._nombre_restaurante(t.restaurante_id)} · {fecha_hora(t.fecha)} · {marca}", t.id))
        return opciones

    def primera_evaluable(self, usuario_id: Any) -> int | None:
        uid = _id(usuario_id)
        if uid is None:
            return None
        evaluables = self.app.controlador_evaluacion.transacciones_evaluables(uid)
        return max((t.id for t in evaluables), default=None)

    def solicitar_evaluacion(self, usuario_id: Any, transaccion_id: Any) -> tuple[str, bool]:
        """Pasos 1–6 de CU-01. Devuelve (mensaje, mostrar_formulario)."""
        try:
            t = self.app.controlador_evaluacion.solicitar_evaluacion(_id(usuario_id), _id(transaccion_id))
        except ErrorDominio as error:
            return aviso(self._mensaje_rechazo(error, transaccion_id)), False
        return (
            ok(
                f"Tu consumo #{t.id} en «{self._nombre_restaurante(t.restaurante_id)}» está completado. "
                "Califícalo y escribe tu comentario."
            ),
            True,
        )

    def _mensaje_rechazo(self, error: ErrorDominio, transaccion_id: Any) -> str:
        """Redacta el motivo de rechazo en el lenguaje de la interfaz («consumo»).

        El dominio entrega un código (``MotivoRechazo``); la presentación decide
        cómo decirlo a la persona usuaria.
        """
        if not isinstance(error, EvaluacionNoPermitida):
            return str(error)
        tid = _id(transaccion_id)
        t = self.app.transacciones.obtener(tid) if tid is not None else None
        mensajes = {
            MotivoRechazo.SIN_TRANSACCION: "No hay un consumo que respalde la evaluación. Registra tu visita primero.",
            MotivoRechazo.TRANSACCION_AJENA: "Solo quien hizo el consumo puede evaluarlo.",
            MotivoRechazo.TRANSACCION_NO_COMPLETADA: (
                f"Tu consumo #{tid} está {t.estado.value if t else 'sin completar'}. "
                "Solo puedes evaluar consumos que el restaurante ya completó."
            ),
            MotivoRechazo.TRANSACCION_CANCELADA: f"Tu consumo #{tid} fue cancelado, así que no se puede evaluar.",
            MotivoRechazo.TRANSACCION_YA_EVALUADA: (
                f"Ya evaluaste el consumo #{tid}. Cada consumo admite una sola evaluación."
            ),
            MotivoRechazo.RESTAURANTE_NO_DISPONIBLE: "Este restaurante no está disponible por ahora; no admite evaluaciones.",
            MotivoRechazo.USUARIO_NO_HABILITADO: "Inicia sesión con una cuenta activa para evaluar.",
        }
        return mensajes.get(error.motivo, str(error))

    def registrar_evaluacion(
        self, usuario_id: Any, transaccion_id: Any, calificacion: Any, comentario: str
    ) -> tuple[str, bool]:
        """Pasos 7–12 de CU-01. Devuelve (mensaje, mantener_formulario_visible)."""
        try:
            e = self.app.controlador_evaluacion.registrar_evaluacion(
                _id(usuario_id), _id(transaccion_id), calificacion, comentario
            )
        except ErrorDominio as error:
            return aviso(self._mensaje_rechazo(error, transaccion_id)), True
        ranking = self.app.ranking.calcular(e.restaurante_id)
        return (
            ok(
                f"Evaluación publicada ({estrellas(e.calificacion)}) y vinculada a tu "
                f"consumo #{e.transaccion_id}. Nueva calificación de "
                f"«{self._nombre_restaurante(e.restaurante_id)}»: {ranking.texto()}."
            ),
            False,
        )

    # ------------------------------------------------------------------ #
    # Locatario (HU-09, HU-10, HU-11 + gestión de transacciones)
    # ------------------------------------------------------------------ #

    def opciones_mis_restaurantes(self, usuario_id: Any) -> list[tuple[str, int]]:
        try:
            restaurantes = self.app.servicio_restaurantes.mis_restaurantes(_id(usuario_id))
        except ErrorDominio:
            return []
        return [(f"{r.nombre}{'' if r.esta_disponible() else ' (suspendido)'}", r.id) for r in restaurantes]

    @capturar_errores(pd.DataFrame(), [])
    def panel_transacciones(self, usuario_id: Any, restaurante_id: Any) -> tuple[str, pd.DataFrame, list]:
        if _id(restaurante_id) is None:
            return "Selecciona uno de tus restaurantes.", pd.DataFrame(), []
        transacciones = self.app.servicio_transacciones.listar_de_restaurante(_id(usuario_id), _id(restaurante_id))
        abiertas = [
            (f"#{t.id} · {dinero(t.importe)} · {t.estado.value}", t.id)
            for t in transacciones
            if not t.estado.es_final
        ]
        mensaje = f"{len(abiertas)} consumo(s) por confirmar o completar." if abiertas else "No hay consumos pendientes."
        return mensaje, self._tabla_transacciones(transacciones, con_cliente=True), abiertas

    @capturar_errores()
    def mover_transaccion(self, usuario_id: Any, transaccion_id: Any, accion: str) -> str:
        servicio = self.app.servicio_transacciones
        operaciones = {
            "confirmar": servicio.confirmar,
            "completar": servicio.completar,
            "cancelar": lambda u, t: servicio.cancelar(u, t, "Cancelada por el restaurante"),
        }
        t = operaciones[accion](_id(usuario_id), _id(transaccion_id))
        extra = " El cliente ya puede evaluar su experiencia." if t.estado is EstadoTransaccion.COMPLETADA else ""
        return ok(f"Consumo #{t.id} → **{t.estado.value}**.{extra}")

    @capturar_errores(pd.DataFrame())
    def evaluaciones_recibidas(self, usuario_id: Any, restaurante_id: Any) -> tuple[str, pd.DataFrame]:
        if _id(restaurante_id) is None:
            return "Selecciona uno de tus restaurantes.", pd.DataFrame()
        evaluaciones = self.app.servicio_restaurantes.evaluaciones_recibidas(_id(usuario_id), _id(restaurante_id))
        tabla = pd.DataFrame(
            [
                [e.id, e.fecha.strftime("%d/%m/%Y"), estrellas(e.calificacion), e.comentario,
                 f"#{e.transaccion_id}", e.estado.value]
                for e in evaluaciones
            ],
            columns=["ID", "Fecha", "Calificación", "Comentario", "Consumo", "Estado"],
        )
        ranking = self.app.ranking.calcular(_id(restaurante_id))
        return f"Calificación actual: **{ranking.texto()}**", tabla

    def datos_formulario(self, restaurante_id: Any) -> list[Any]:
        """Valores para precargar el formulario de edición (HU-10)."""
        r: Restaurante | None = self.app.restaurantes.obtener(_id(restaurante_id) or -1)
        if r is None:
            return [""] * 6 + [[], "", "", [], 0, ""]
        return [
            r.nombre, r.descripcion, r.categoria, r.ubicacion.direccion, r.ubicacion.zona,
            f"{r.ubicacion.latitud}, {r.ubicacion.longitud}",
            [DIAS_SEMANA[d] for d in sorted(r.horario.dias)],
            r.horario.apertura.strftime("%H:%M"), r.horario.cierre.strftime("%H:%M"),
            sorted(r.formas_pago), float(r.precio_promedio), r.fecha_apertura.isoformat(),
        ]

    @staticmethod
    def _datos(
        nombre: str, descripcion: str, categoria: str, direccion: str, zona: str, coordenadas: str,
        dias: list[str], apertura: str, cierre: str, formas_pago: list[str], precio: Any, fecha_apertura: str,
    ) -> DatosRestaurante:
        try:
            latitud, longitud = (float(x) for x in (coordenadas or "").split(","))
        except ValueError as exc:
            raise DatosInvalidos("Escribe las coordenadas como «latitud, longitud».") from exc
        return DatosRestaurante(
            nombre=nombre, descripcion=descripcion, categoria=categoria, direccion=direccion,
            latitud=latitud, longitud=longitud, zona=zona,
            dias=[DIAS_SEMANA.index(d) for d in (dias or [])],
            apertura=apertura, cierre=cierre, formas_pago=formas_pago or [],
            precio_promedio=precio, fecha_apertura=fecha_apertura,
        )

    @capturar_errores()
    def guardar_restaurante(self, usuario_id: Any, restaurante_id: Any, *campos: Any) -> str:
        datos = self._datos(*campos)
        if _id(restaurante_id) is None:
            r = self.app.servicio_restaurantes.registrar(_id(usuario_id), datos)
            return ok(f"Restaurante «{r.nombre}» registrado con el ID {r.id}. Ya aparece en las búsquedas.")
        r = self.app.servicio_restaurantes.actualizar(_id(usuario_id), _id(restaurante_id), datos)
        return ok(f"Información de «{r.nombre}» actualizada.")

    @capturar_errores()
    def agregar_producto(self, usuario_id: Any, restaurante_id: Any, nombre: str, precio: Any, descripcion: str) -> str:
        p = self.app.servicio_restaurantes.agregar_producto(_id(usuario_id), _id(restaurante_id), nombre, precio, descripcion)
        return ok(f"Producto «{p.nombre}» agregado al menú ({dinero(p.precio)}).")

    @capturar_errores()
    def agregar_promocion(self, usuario_id: Any, restaurante_id: Any, descripcion: str, inicio: str, fin: str, condiciones: str) -> str:
        p = self.app.servicio_restaurantes.agregar_promocion(
            _id(usuario_id), _id(restaurante_id), descripcion, inicio, fin, condiciones
        )
        return ok(f"Promoción «{p.descripcion}» publicada del {p.inicio:%d/%m} al {p.fin:%d/%m/%Y}.")

    # ------------------------------------------------------------------ #
    # Administración
    # ------------------------------------------------------------------ #

    @capturar_errores(pd.DataFrame(), pd.DataFrame(), [], [])
    def panel_admin(self, usuario_id: Any) -> tuple[str, pd.DataFrame, pd.DataFrame, list, list]:
        evaluaciones = self.app.servicio_restaurantes.todas_las_evaluaciones(_id(usuario_id))
        restaurantes = self.app.restaurantes.listar()
        tabla_r = pd.DataFrame(
            [[r.id, r.nombre, r.categoria, r.estado.value, self.app.ranking.calcular(r.id).texto()] for r in restaurantes],
            columns=["ID", "Restaurante", "Tipo", "Estado", "Calificación"],
        )
        tabla_e = pd.DataFrame(
            [
                [e.id, self._nombre_restaurante(e.restaurante_id), estrellas(e.calificacion), e.comentario,
                 f"#{e.transaccion_id}", e.estado.value, e.motivo_moderacion]
                for e in evaluaciones
            ],
            columns=["ID", "Restaurante", "Calificación", "Comentario", "Consumo", "Estado", "Motivo"],
        )
        opciones_r = [(f"{r.nombre} ({r.estado.value})", r.id) for r in restaurantes]
        opciones_e = [(f"#{e.id} · {self._nombre_restaurante(e.restaurante_id)} · {e.estado.value}", e.id) for e in evaluaciones]
        return "Panel de administración.", tabla_r, tabla_e, opciones_r, opciones_e

    @capturar_errores()
    def cambiar_estado_restaurante(self, usuario_id: Any, restaurante_id: Any, activo: bool) -> str:
        estado = EstadoRestaurante.ACTIVO if activo else EstadoRestaurante.SUSPENDIDO
        r = self.app.servicio_restaurantes.cambiar_estado(_id(usuario_id), _id(restaurante_id), estado)
        return ok(f"«{r.nombre}» ahora está {r.estado.value}.")

    @capturar_errores()
    def moderar_evaluacion(self, usuario_id: Any, evaluacion_id: Any, ocultar: bool, motivo: str) -> str:
        servicio = self.app.servicio_restaurantes
        if ocultar:
            e = servicio.ocultar_evaluacion(_id(usuario_id), _id(evaluacion_id), motivo)
            return ok(f"Evaluación #{e.id} ocultada. Ya no cuenta para el ranking.")
        e = servicio.restaurar_evaluacion(_id(usuario_id), _id(evaluacion_id))
        return ok(f"Evaluación #{e.id} restaurada.")


def fecha_hoy_mas(dias: int, base: date) -> str:
    return (base + timedelta(days=dias)).isoformat()
