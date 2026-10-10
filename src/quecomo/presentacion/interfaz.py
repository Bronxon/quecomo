"""Interfaz web de ¿Qué Como? construida con Gradio (capa de PRESENTACIÓN).

Esta capa solo muestra información y envía solicitudes. No contiene reglas
de negocio: todas las decisiones (¿puede evaluarse?, ¿quién confirma una
transacción?) las toman el dominio y la capa de aplicación.
"""

from __future__ import annotations

from typing import Any

import gradio as gr

from ..aplicacion.servicio_busqueda import MAXIMO_COMPARACION, Orden
from ..configuracion import Aplicacion, crear_aplicacion
from ..dominio.entidades import DIAS_SEMANA, LONGITUD_MAXIMA_COMENTARIO
from ..infraestructura.datos_demo import CREDITO, DEBITO, EFECTIVO, TRANSFERENCIA
from .vista import (
    HORARIO_CUALQUIERA,
    OPCIONES_HORARIO,
    SIN_REFERENCIA,
    TODAS,
    Vista,
    fecha_hoy_mas,
)

TEMA = gr.themes.Soft(
    primary_hue="orange",
    secondary_hue="amber",
    neutral_hue="stone",
    font=[gr.themes.GoogleFont("Nunito"), "ui-sans-serif", "system-ui", "sans-serif"],
)

CSS = """
#encabezado { text-align: center; padding: 18px 8px 4px; }
#encabezado h1 { font-size: 2.4rem; margin: 0; letter-spacing: -0.5px; }
#encabezado p { margin: 6px 0 0; opacity: .8; }
.mensaje p { font-size: 1rem; }
footer { display: none !important; }
"""

ENCABEZADO = """
<div id="encabezado">
  <h1>🍽️ ¿Qué Como?</h1>
  <p>Convertir la búsqueda de un restaurante en una decisión informada.</p>
  <p><small>Prototipo académico (MVP) · Todos los datos son ficticios</small></p>
</div>
"""

ACERCA_DE = """
## ¿Cómo funciona la regla de confianza?

En ¿Qué Como? **una evaluación solo existe si la respalda una transacción real**:

1. El **cliente** registra una transacción con un restaurante → queda **PENDIENTE**.
2. El **locatario** la **confirma** y, al concluir el servicio, la **completa**.
3. Solo entonces el cliente puede **evaluar**, y **una sola vez** por transacción.

```
INICIADA → PENDIENTE → CONFIRMADA → COMPLETADA ──► habilita 1 evaluación
               └────────────┴──► CANCELADA (no habilita evaluación)
```

El cliente **no puede** completar su propia transacción y el administrador
tampoco puede fabricarla: así nadie se habilita una evaluación a sí mismo.

### Para probar en 1 minuto
1. Con **Ana López** entra a **⭐ Evaluar**: la transacción con *Tacos La Lumbre* ya es evaluable.
2. Elige una transacción **PENDIENTE** o **CANCELADA** y observa el rechazo con su motivo.
3. Registra una transacción nueva en **🧾 Mis transacciones**, cambia la sesión a
   **Héctor Salas (Locatario)**, confírmala y complétala en **🏪 Locatario**, y vuelve a Ana para evaluarla.

### Limitaciones del prototipo
- El inicio de sesión es **simulado** (se elige un usuario de demostración).
- Los datos viven **en memoria**: se reinician al reiniciar la aplicación.
- La «transacción» es un registro declarado, no un cobro real. Ver `docs/` en el repositorio.
"""


def construir_interfaz(app: Aplicacion | None = None) -> gr.Blocks:
    vista = Vista(app or crear_aplicacion())
    hoy = vista.app.reloj().date()
    usuario_inicial = 1
    formas_pago = [EFECTIVO, DEBITO, CREDITO, TRANSFERENCIA]

    with gr.Blocks(title="¿Qué Como?", analytics_enabled=False) as demo:
        gr.HTML(ENCABEZADO)
        with gr.Row(equal_height=True):
            usuario = gr.Dropdown(
                vista.opciones_usuarios(),
                value=usuario_inicial,
                label="👤 Sesión de demostración",
                info="Inicio de sesión simulado: elige con qué usuario probar la app.",
                scale=2,
            )
            bienvenida = gr.Markdown(vista.bienvenida(usuario_inicial))

        with gr.Tabs():
            # ------------------------------------------------------------ #
            with gr.Tab("🔎 Buscar"):
                with gr.Row():
                    with gr.Column(scale=1, min_width=270):
                        b_texto = gr.Textbox(label="¿Qué se te antoja?", placeholder="tacos, sushi, café…")
                        b_categoria = gr.Dropdown(vista.opciones_categorias(), value=TODAS, label="Tipo de comida")
                        b_precio = gr.Slider(50, 600, value=600, step=10, label="Precio promedio máximo (MXN)")
                        b_punto = gr.Dropdown(vista.opciones_puntos(), value="Centro", label="Punto de referencia")
                        b_distancia = gr.Slider(0.5, 15, value=15, step=0.5, label="Distancia máxima (km)")
                        b_horario = gr.Dropdown(OPCIONES_HORARIO, value=HORARIO_CUALQUIERA, label="Horario")
                        b_pago = gr.Dropdown(vista.opciones_formas_pago(), value=TODAS, label="Forma de pago")
                        b_calificacion = gr.Slider(0, 5, value=0, step=0.5, label="Calificación mínima")
                        b_promo = gr.Checkbox(label="Solo con promoción vigente")
                        b_orden = gr.Radio([o.value for o in Orden], value=Orden.RANKING.value, label="Ordenar por")
                        b_boton = gr.Button("Buscar", variant="primary")
                    with gr.Column(scale=3):
                        b_resumen = gr.Markdown(elem_classes="mensaje")
                        b_tabla = gr.Dataframe(interactive=False, wrap=True, label="Resultados")
                        gr.Markdown(
                            "<small>La calificación solo incluye evaluaciones respaldadas por una "
                            "transacción completada. El orden por ranking usa un promedio ponderado "
                            "para no favorecer a quien tiene muy pocas evaluaciones.</small>"
                        )
                filtros = [b_texto, b_categoria, b_precio, b_punto, b_distancia, b_horario,
                           b_pago, b_calificacion, b_promo, b_orden]

            # ------------------------------------------------------------ #
            with gr.Tab("📋 Ficha del restaurante"):
                with gr.Row():
                    f_restaurante = gr.Dropdown(vista.opciones_restaurantes(), label="Restaurante", scale=2)
                    f_punto = gr.Dropdown(vista.opciones_puntos(), value="Centro", label="Punto de referencia")
                f_info = gr.Markdown()
                f_menu = gr.Dataframe(interactive=False, wrap=True, label="Menú")

            # ------------------------------------------------------------ #
            with gr.Tab("⚖️ Comparar"):
                with gr.Row():
                    c_restaurantes = gr.Dropdown(
                        vista.opciones_restaurantes(),
                        multiselect=True,
                        max_choices=MAXIMO_COMPARACION,
                        label=f"Elige de 2 a {MAXIMO_COMPARACION} restaurantes",
                        scale=3,
                    )
                    c_punto = gr.Dropdown(vista.opciones_puntos(), value="Centro", label="Punto de referencia")
                c_boton = gr.Button("Comparar", variant="primary")
                c_mensaje = gr.Markdown(elem_classes="mensaje")
                c_tabla = gr.Dataframe(interactive=False, wrap=True, label="Comparación")

            # ------------------------------------------------------------ #
            with gr.Tab("🧾 Mis transacciones"):
                gr.Markdown(
                    "Registra tu consumo en un restaurante. Queda **PENDIENTE** hasta que el "
                    "restaurante lo confirme y lo complete; solo entonces podrás evaluar."
                )
                with gr.Row():
                    t_restaurante = gr.Dropdown(vista.opciones_restaurantes(), label="Restaurante", scale=2)
                    t_importe = gr.Number(label="Importe (MXN)", value=250, minimum=1)
                    t_boton = gr.Button("Registrar transacción", variant="primary")
                t_mensaje = gr.Markdown(elem_classes="mensaje")
                t_tabla = gr.Dataframe(interactive=False, wrap=True, label="Mis transacciones")
                with gr.Row():
                    t_cancelable = gr.Dropdown([], label="Transacción a cancelar", scale=2)
                    t_cancelar = gr.Button("Cancelar transacción", variant="stop")

            # ------------------------------------------------------------ #
            with gr.Tab("⭐ Evaluar"):
                gr.Markdown(
                    "**Caso de uso CU-01.** Elige una de tus transacciones. El sistema verifica que esté "
                    "**COMPLETADA** y que no se haya evaluado antes. Puedes elegir una que no cumpla "
                    "para ver cómo se rechaza."
                )
                with gr.Row():
                    e_transaccion = gr.Dropdown([], label="Transacción", scale=3)
                    e_validar = gr.Button("Evaluar restaurante", variant="primary")
                e_mensaje = gr.Markdown(elem_classes="mensaje")
                with gr.Group(visible=False) as e_formulario:
                    e_calificacion = gr.Radio(
                        [("★ 1", 1), ("★★ 2", 2), ("★★★ 3", 3), ("★★★★ 4", 4), ("★★★★★ 5", 5)],
                        label="Calificación",
                    )
                    e_comentario = gr.Textbox(
                        label="Comentario",
                        lines=3,
                        max_lines=6,
                        placeholder="¿Qué tal la comida, el servicio y el lugar? (mínimo 10 caracteres)",
                        max_length=LONGITUD_MAXIMA_COMENTARIO,
                    )
                    e_registrar = gr.Button("Registrar evaluación", variant="primary")

            # ------------------------------------------------------------ #
            with gr.Tab("🏪 Locatario"):
                gr.Markdown("Sección para **locatarios**. Con otro rol, el sistema rechazará las operaciones.")
                l_restaurante = gr.Dropdown([], label="Mi restaurante")
                with gr.Tabs():
                    with gr.Tab("Transacciones"):
                        l_mensaje_t = gr.Markdown(elem_classes="mensaje")
                        l_tabla_t = gr.Dataframe(interactive=False, wrap=True)
                        with gr.Row():
                            l_transaccion = gr.Dropdown([], label="Transacción por gestionar", scale=2)
                            l_confirmar = gr.Button("Confirmar")
                            l_completar = gr.Button("Completar", variant="primary")
                            l_cancelar = gr.Button("Cancelar", variant="stop")
                    with gr.Tab("Evaluaciones recibidas"):
                        l_mensaje_e = gr.Markdown()
                        l_tabla_e = gr.Dataframe(interactive=False, wrap=True)
                    with gr.Tab("Información del restaurante"):
                        with gr.Row():
                            l_nombre = gr.Textbox(label="Nombre")
                            l_categoria = gr.Textbox(label="Tipo de comida")
                            l_precio = gr.Number(label="Precio promedio por persona (MXN)")
                        l_descripcion = gr.Textbox(label="Descripción", lines=2)
                        with gr.Row():
                            l_direccion = gr.Textbox(label="Dirección")
                            l_zona = gr.Textbox(label="Zona")
                            l_coordenadas = gr.Textbox(label="Coordenadas (latitud, longitud)")
                        with gr.Row():
                            l_dias = gr.CheckboxGroup(list(DIAS_SEMANA), label="Días de servicio")
                            l_apertura = gr.Textbox(label="Apertura (HH:MM)")
                            l_cierre = gr.Textbox(label="Cierre (HH:MM)")
                        with gr.Row():
                            l_pagos = gr.CheckboxGroup(formas_pago, label="Formas de pago")
                            l_fecha = gr.Textbox(label="Fecha de apertura (AAAA-MM-DD)")
                        with gr.Row():
                            l_guardar = gr.Button("Guardar cambios", variant="primary")
                            l_nuevo = gr.Button("Registrar como restaurante nuevo")
                        l_mensaje_i = gr.Markdown(elem_classes="mensaje")
                    with gr.Tab("Menú y promociones"):
                        gr.Markdown("#### Agregar producto al menú")
                        with gr.Row():
                            l_p_nombre = gr.Textbox(label="Producto")
                            l_p_precio = gr.Number(label="Precio (MXN)", minimum=1)
                            l_p_descripcion = gr.Textbox(label="Descripción")
                        l_p_boton = gr.Button("Agregar producto")
                        gr.Markdown("#### Publicar promoción")
                        with gr.Row():
                            l_r_descripcion = gr.Textbox(label="Promoción")
                            l_r_inicio = gr.Textbox(label="Inicio (AAAA-MM-DD)", value=hoy.isoformat())
                            l_r_fin = gr.Textbox(label="Fin (AAAA-MM-DD)", value=fecha_hoy_mas(30, hoy))
                        l_r_condiciones = gr.Textbox(label="Condiciones")
                        l_r_boton = gr.Button("Publicar promoción")
                        l_mensaje_m = gr.Markdown(elem_classes="mensaje")
                formulario = [l_nombre, l_descripcion, l_categoria, l_direccion, l_zona, l_coordenadas,
                              l_dias, l_apertura, l_cierre, l_pagos, l_precio, l_fecha]

            # ------------------------------------------------------------ #
            with gr.Tab("🛡️ Administración"):
                a_mensaje = gr.Markdown(elem_classes="mensaje")
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### Restaurantes")
                        a_tabla_r = gr.Dataframe(interactive=False, wrap=True)
                        a_restaurante = gr.Dropdown([], label="Restaurante")
                        with gr.Row():
                            a_activar = gr.Button("Activar")
                            a_suspender = gr.Button("Suspender", variant="stop")
                    with gr.Column():
                        gr.Markdown("#### Moderación de evaluaciones")
                        a_tabla_e = gr.Dataframe(interactive=False, wrap=True)
                        a_evaluacion = gr.Dropdown([], label="Evaluación")
                        a_motivo = gr.Textbox(label="Motivo de moderación (obligatorio para ocultar)")
                        with gr.Row():
                            a_ocultar = gr.Button("Ocultar", variant="stop")
                            a_restaurar = gr.Button("Restaurar")

            # ------------------------------------------------------------ #
            with gr.Tab("ℹ️ Acerca de"):
                gr.Markdown(ACERCA_DE)

        # ================================================================ #
        # Eventos
        # ================================================================ #

        def refrescar_catalogos() -> tuple[Any, ...]:
            opciones = vista.opciones_restaurantes()
            return (
                gr.update(choices=opciones),
                gr.update(choices=opciones),
                gr.update(choices=opciones),
                gr.update(choices=vista.opciones_categorias()),
                gr.update(choices=vista.opciones_formas_pago()),
            )

        catalogos = [f_restaurante, c_restaurantes, t_restaurante, b_categoria, b_pago]

        def refrescar_cliente(uid: Any) -> tuple[Any, ...]:
            return (
                vista.mis_transacciones(uid),
                gr.update(choices=vista.opciones_cancelables(uid), value=None),
                gr.update(choices=vista.opciones_para_evaluar(uid), value=vista.primera_evaluable(uid)),
            )

        salidas_cliente = [t_tabla, t_cancelable, e_transaccion]

        def refrescar_admin(uid: Any) -> tuple[Any, ...]:
            mensaje, tabla_r, tabla_e, opciones_r, opciones_e = vista.panel_admin(uid)
            return mensaje, tabla_r, tabla_e, gr.update(choices=opciones_r, value=None), gr.update(choices=opciones_e, value=None)

        salidas_admin = [a_mensaje, a_tabla_r, a_tabla_e, a_restaurante, a_evaluacion]

        def cambiar_usuario(uid: Any) -> tuple[Any, ...]:
            mis = vista.opciones_mis_restaurantes(uid)
            return (
                vista.bienvenida(uid),
                *refrescar_cliente(uid),
                "",
                gr.update(visible=False),
                gr.update(choices=mis, value=mis[0][1] if mis else None),
                *refrescar_admin(uid),
            )

        salidas_usuario = [bienvenida, *salidas_cliente, e_mensaje, e_formulario, l_restaurante, *salidas_admin]
        usuario.change(cambiar_usuario, usuario, salidas_usuario)

        # Buscar
        gr.on([b_boton.click, *(f.change for f in filtros)], vista.buscar, filtros, [b_tabla, b_resumen])

        # Ficha
        gr.on([f_restaurante.change, f_punto.change], vista.ficha, [f_restaurante, f_punto], [f_info, f_menu])

        # Comparar
        c_boton.click(vista.comparar, [c_restaurantes, c_punto], [c_mensaje, c_tabla])

        # Mis transacciones
        t_boton.click(vista.registrar_transaccion, [usuario, t_restaurante, t_importe], t_mensaje).then(
            refrescar_cliente, usuario, salidas_cliente
        )
        t_cancelar.click(vista.cancelar_transaccion, [usuario, t_cancelable], t_mensaje).then(
            refrescar_cliente, usuario, salidas_cliente
        )

        # Evaluar (CU-01)
        def validar(uid: Any, tid: Any) -> tuple[Any, ...]:
            mensaje, mostrar = vista.solicitar_evaluacion(uid, tid)
            return mensaje, gr.update(visible=mostrar), None, ""

        e_validar.click(validar, [usuario, e_transaccion], [e_mensaje, e_formulario, e_calificacion, e_comentario])
        e_transaccion.change(lambda: ("", gr.update(visible=False)), None, [e_mensaje, e_formulario])

        def registrar(uid: Any, tid: Any, calificacion: Any, comentario: str) -> tuple[Any, ...]:
            mensaje, visible = vista.registrar_evaluacion(uid, tid, calificacion, comentario)
            return mensaje, gr.update(visible=visible)

        e_registrar.click(
            registrar, [usuario, e_transaccion, e_calificacion, e_comentario], [e_mensaje, e_formulario]
        ).success(
            lambda uid: (vista.mis_transacciones(uid), gr.update(choices=vista.opciones_para_evaluar(uid))),
            usuario,
            [t_tabla, e_transaccion],
        )

        # Locatario
        def cargar_locatario(uid: Any, rid: Any) -> tuple[Any, ...]:
            mensaje_t, tabla_t, abiertas = vista.panel_transacciones(uid, rid)
            mensaje_e, tabla_e = vista.evaluaciones_recibidas(uid, rid)
            return (
                mensaje_t, tabla_t, gr.update(choices=abiertas, value=None),
                mensaje_e, tabla_e, *vista.datos_formulario(rid),
            )

        salidas_locatario = [l_mensaje_t, l_tabla_t, l_transaccion, l_mensaje_e, l_tabla_e, *formulario]
        l_restaurante.change(cargar_locatario, [usuario, l_restaurante], salidas_locatario)

        for boton, accion in ((l_confirmar, "confirmar"), (l_completar, "completar"), (l_cancelar, "cancelar")):
            def mover(uid: Any, rid: Any, tid: Any, _accion: str = accion) -> tuple[Any, ...]:
                resultado = vista.mover_transaccion(uid, tid, _accion)
                _, tabla, abiertas = vista.panel_transacciones(uid, rid)
                return resultado, tabla, gr.update(choices=abiertas, value=None)

            boton.click(mover, [usuario, l_restaurante, l_transaccion], [l_mensaje_t, l_tabla_t, l_transaccion])

        def guardar(uid: Any, rid: Any, nuevo: bool, *campos: Any) -> tuple[Any, ...]:
            mensaje = vista.guardar_restaurante(uid, None if nuevo else rid, *campos)
            mis = vista.opciones_mis_restaurantes(uid)
            return mensaje, gr.update(choices=mis), *refrescar_catalogos()

        salidas_guardar = [l_mensaje_i, l_restaurante, *catalogos]
        l_guardar.click(lambda u, r, *c: guardar(u, r, False, *c), [usuario, l_restaurante, *formulario], salidas_guardar)
        l_nuevo.click(lambda u, r, *c: guardar(u, r, True, *c), [usuario, l_restaurante, *formulario], salidas_guardar)

        l_p_boton.click(
            vista.agregar_producto, [usuario, l_restaurante, l_p_nombre, l_p_precio, l_p_descripcion], l_mensaje_m
        )
        l_r_boton.click(
            vista.agregar_promocion,
            [usuario, l_restaurante, l_r_descripcion, l_r_inicio, l_r_fin, l_r_condiciones],
            l_mensaje_m,
        )

        # Administración
        def estado_restaurante(uid: Any, rid: Any, activo: bool) -> tuple[Any, ...]:
            mensaje = vista.cambiar_estado_restaurante(uid, rid, activo)
            _, tabla_r, tabla_e, opciones_r, opciones_e = refrescar_admin(uid)
            return mensaje, tabla_r, tabla_e, opciones_r, opciones_e, *refrescar_catalogos()

        a_activar.click(lambda u, r: estado_restaurante(u, r, True), [usuario, a_restaurante], [*salidas_admin, *catalogos])
        a_suspender.click(lambda u, r: estado_restaurante(u, r, False), [usuario, a_restaurante], [*salidas_admin, *catalogos])

        def moderar(uid: Any, eid: Any, motivo: str, ocultar: bool) -> tuple[Any, ...]:
            mensaje = vista.moderar_evaluacion(uid, eid, ocultar, motivo)
            _, tabla_r, tabla_e, opciones_r, opciones_e = refrescar_admin(uid)
            return mensaje, tabla_r, tabla_e, opciones_r, opciones_e

        a_ocultar.click(lambda u, e, m: moderar(u, e, m, True), [usuario, a_evaluacion, a_motivo], salidas_admin)
        a_restaurar.click(lambda u, e, m: moderar(u, e, m, False), [usuario, a_evaluacion, a_motivo], salidas_admin)

        # Carga inicial
        demo.load(cambiar_usuario, usuario, salidas_usuario)
        demo.load(vista.buscar, filtros, [b_tabla, b_resumen])

    return demo


__all__ = ["CSS", "SIN_REFERENCIA", "TEMA", "construir_interfaz"]
