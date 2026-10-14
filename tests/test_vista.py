"""Pruebas de la capa de presentación (sin levantar el servidor)."""

import gradio as gr
import pytest

from quecomo.dominio.excepciones import (
    EvaluacionNoPermitida,
    MotivoRechazo,
)
from quecomo.presentacion.interfaz import construir_interfaz
from quecomo.presentacion.vista import HORARIO_AHORA, TODAS, Vista, estrellas

@pytest.fixture
def vista(app_demo):
    return Vista(app_demo)


def test_la_interfaz_se_construye(app_demo):
    assert isinstance(construir_interfaz(app_demo), gr.Blocks)


def test_estrellas():
    assert estrellas(4.5) == "★★★★★"
    assert estrellas(4.4) == "★★★★☆"
    assert estrellas(None) == "—"


def test_buscar(vista):
    tabla, resumen = vista.buscar("", TODAS, 600, "Centro", 15, HORARIO_AHORA, TODAS, 0, False, "Mejor ranking")
    assert "restaurante(s)" in resumen
    assert set(tabla["Abierto"]) == {"Sí"}


def test_ficha_muestra_evaluaciones_con_trazabilidad(vista):
    texto, menu = vista.ficha(1, "Centro")
    assert "Respaldada por el consumo" in texto
    assert "Ana L." in texto  # nombre público, no el nombre completo
    assert "Ana López" not in texto
    assert len(menu) == 4


def test_comparar_con_un_solo_restaurante_muestra_aviso(vista):
    mensaje, _ = vista.comparar([1], "Centro")
    assert mensaje.startswith("⛔")


def test_flujo_cu01_desde_la_vista(vista):
    """Ana (id 1) tiene la transacción #2 lista para evaluar en los datos demo."""
    assert vista.primera_evaluable(1) == 2
    mensaje, mostrar = vista.solicitar_evaluacion(1, 2)
    assert mostrar and mensaje.startswith("✅")
    mensaje, visible = vista.registrar_evaluacion(1, 2, 4, "Muy buenos tacos al carbón.")
    assert mensaje.startswith("✅") and not visible
    mensaje, mostrar = vista.solicitar_evaluacion(1, 2)
    assert not mostrar and "Ya evaluaste" in mensaje


def test_rechazo_de_transaccion_pendiente(vista):
    pendiente = next(t for t in vista.app.transacciones.listar_por_usuario(1) if t.estado.value == "PENDIENTE")
    mensaje, mostrar = vista.solicitar_evaluacion(1, pendiente.id)
    assert not mostrar and "PENDIENTE" in mensaje


def test_cliente_no_completa_desde_panel_locatario(vista):
    mensaje = vista.mover_transaccion(1, 6, "completar")
    assert mensaje.startswith("⛔")


def test_locatario_completa_y_cliente_evalua(vista):
    registro = vista.registrar_transaccion(1, 1, 300)
    assert registro.startswith("✅")
    tid = max(t.id for t in vista.app.transacciones.listar_por_usuario(1))
    assert vista.mover_transaccion(4, tid, "confirmar").startswith("✅")
    assert "ya puede evaluar" in vista.mover_transaccion(4, tid, "completar")
    assert vista.solicitar_evaluacion(1, tid)[1]


def test_panel_admin_restringido(vista):
    assert vista.panel_admin(1)[0].startswith("⛔")
    assert vista.panel_admin(7)[0] == "Panel de administración."


def test_formulario_del_locatario(vista):
    campos = vista.datos_formulario(1)
    assert campos[0] == "Mariscos El Faro Azul"
    campos[0] = "Mariscos El Faro Azul Renovado"
    assert vista.guardar_restaurante(4, 1, *campos).startswith("✅")
    assert vista.app.restaurantes.obtener(1).nombre.endswith("Renovado")


def test_rn07_interfaz_sin_pagos_en_linea(vista):
    assert "Transferencia" not in vista.opciones_formas_pago()
    texto, _ = vista.ficha(2, "Centro")
    assert "Formas de pago en el local:** Efectivo" in texto
    campos = vista.datos_formulario(1)
    campos[9] = ["Efectivo", "Transferencia"]
    mensaje = vista.guardar_restaurante(4, 1, *campos)
    assert mensaje.startswith("⛔") and "pagos en línea" in mensaje


def test_la_interfaz_no_tiene_pestana_de_transacciones(app_demo):
    """Observación de revisión: el registro de consumo vive dentro de «Evaluar»."""
    demo = construir_interfaz(app_demo)
    pestanas = [b.label for b in demo.blocks.values() if isinstance(b, gr.Tab)]
    assert not any("transaccion" in (p or "").lower() for p in pestanas)
    assert "Evaluar" in pestanas


def test_motivos_de_rechazo_en_lenguaje_de_interfaz(vista):
    cancelada = next(t for t in vista.app.transacciones.listar_por_usuario(1) if t.estado.value == "CANCELADA")
    mensaje, mostrar = vista.solicitar_evaluacion(1, cancelada.id)
    assert not mostrar and "fue cancelado" in mensaje
    mensaje, _ = vista.solicitar_evaluacion(1, None)
    assert "Registra tu visita" in mensaje

def test_bienvenida_usuario_inexistente(vista):
    assert vista.bienvenida(None) == "Selecciona un usuario de demostración."


def test_rol_usuario_inexistente(vista):
    assert vista.rol_de(None) is None


def test_momento_sin_horario(vista):
    assert vista._momento(None) is None
    assert vista._momento("") is None
    assert vista._momento("Cualquier horario") is None


def test_ficha_sin_restaurante_seleccionado(vista):
    texto, menu = vista.ficha(None, "Centro")
    assert texto == "Selecciona un restaurante para ver su información."
    assert menu.empty


def test_datos_formulario_restaurante_inexistente(vista):
    campos = vista.datos_formulario(-999)
    assert campos == [""] * 6 + [[], "", "", [], 0, ""]


def test_opciones_cancelables_sin_usuario(vista):
    assert vista.opciones_cancelables(None) == []


def test_primera_evaluable_sin_usuario(vista):
    assert vista.primera_evaluable(None) is None


def test_nombre_restaurante_inexistente(vista):
    assert vista._nombre_restaurante(-999) == "#-999"


def test_tabla_transacciones_vacia(vista):
    tabla = vista._tabla_transacciones([])
    assert tabla.empty
    assert list(tabla.columns) == [
        "ID", "Fecha", "Restaurante", "Importe", "Estado", "Evaluada"
    ]

def test_datos_rechaza_coordenadas_invalidas():
    from quecomo.dominio.excepciones import DatosInvalidos

    with pytest.raises(DatosInvalidos):
        Vista._datos(
            "Restaurante de prueba",
            "Descripción",
            "Mexicana",
            "Dirección de prueba",
            "Centro",
            "coordenadas-invalidas",
            ["Lunes"],
            "09:00",
            "18:00",
            ["Efectivo"],
            150,
            "2025-01-01",
        )

def test_moderar_evaluacion_oculta_y_restaurar(vista):
    evaluaciones = vista.app.servicio_restaurantes.todas_las_evaluaciones(7)
    assert evaluaciones, "Se necesitan evaluaciones de demostración."

    evaluacion = evaluaciones[0]

    mensaje = vista.moderar_evaluacion(
        7, evaluacion.id, True, "Prueba de moderación"
    )
    assert mensaje.startswith("✅")
    assert "ocultada" in mensaje

    mensaje = vista.moderar_evaluacion(
        7, evaluacion.id, False, ""
    )
    assert mensaje.startswith("✅")
    assert "restaurada" in mensaje
    
def test_agregar_producto_desde_vista(vista):
    productos_antes = vista.app.restaurantes.obtener(1).productos()
    cantidad_antes = len(productos_antes)

    mensaje = vista.agregar_producto(
        4, 1, "Taco de prueba", 45, "Taco para pruebas automatizadas"
    )

    assert mensaje.startswith("✅")
    assert "Taco de prueba" in mensaje
    assert "$45.00" in mensaje

    productos_despues = vista.app.restaurantes.obtener(1).productos()
    assert len(productos_despues) == cantidad_antes + 1
    assert any(p.nombre == "Taco de prueba" for p in productos_despues)

def test_agregar_promocion_desde_vista(vista):
    mensaje = vista.agregar_promocion(
        4,
        1,
        "Promoción de prueba",
        "2026-10-14",
        "2026-10-31",
        "Válida durante las pruebas",
    )

    assert mensaje.startswith("✅")
    assert "Promoción de prueba" in mensaje
    assert "14/10" in mensaje
    assert "31/10/2026" in mensaje

def test_agregar_promocion_con_fechas_invertidas(vista):
    mensaje = vista.agregar_promocion(
        4,
        1,
        "Promoción inválida",
        "2026-10-31",
        "2026-10-14",
        "Prueba de fechas invertidas",
    )

    assert mensaje.startswith("⛔")

def test_agregar_promocion_sin_permisos(vista):
    mensaje = vista.agregar_promocion(
        1,
        1,
        "Promoción no autorizada",
        "2026-10-14",
        "2026-10-31",
        "Prueba de permisos",
    )

    assert mensaje.startswith("⛔")


def test_agregar_promocion_restaurante_inexistente(vista):
    mensaje = vista.agregar_promocion(
        4,
        -999,
        "Promoción sin restaurante",
        "2026-10-14",
        "2026-10-31",
        "Prueba de restaurante inexistente",
    )

    assert mensaje.startswith("⛔")

def test_agregar_producto_sin_permisos(vista):
    mensaje = vista.agregar_producto(
        1,
        1,
        "Producto no autorizado",
        45,
        "Prueba de permisos",
    )

    assert mensaje.startswith("⛔")


def test_agregar_producto_restaurante_inexistente(vista):
    mensaje = vista.agregar_producto(
        4,
        -999,
        "Producto sin restaurante",
        45,
        "Prueba de restaurante inexistente",
    )

    assert mensaje.startswith("⛔")
    
def test_comparar_sin_restaurantes_seleccionados(vista):
    mensaje, tabla = vista.comparar([], "Centro")

    assert mensaje.startswith("⛔")
    assert "Selecciona al menos dos restaurantes" in mensaje
    assert tabla.empty


def test_comparar_ignora_ids_invalidos(vista):
    mensaje, tabla = vista.comparar([None, -999], "Centro")

    assert mensaje.startswith("⛔")
    assert "Selecciona al menos dos restaurantes" in mensaje
    assert tabla.empty
    
def test_comparar_con_ids_inexistentes(vista):
    mensaje, tabla = vista.comparar([-999, -998], "Centro")

    assert mensaje.startswith("⛔")
    assert "no existe" in mensaje
    assert tabla.empty

def test_comparar_con_restaurantes_muestra_resultado(vista):
    mensaje, tabla = vista.comparar([1, 2], "Centro")

    assert mensaje.startswith("✅")
    assert "Comparando" in mensaje
    assert "Mejor calificado:" in mensaje
    assert not tabla.empty
    assert "Criterio" in tabla.columns

def test_id_retorna_none_para_valores_vacios():
    from quecomo.presentacion.vista import _id

    assert _id(None) is None
    assert _id("") is None
    assert _id([]) is None


def test_id_convierte_cadena_numerica():
    from quecomo.presentacion.vista import _id

    assert _id("123") == 123
    assert _id(45) == 45
    
def test_fecha_hora_formatea_fecha_y_hora():
    from datetime import datetime

    from quecomo.presentacion.vista import fecha_hora

    valor = datetime(2026, 10, 14, 9, 5)

    assert fecha_hora(valor) == "14/10/2026 09:05"
    
def test_momento_horario_que_ya_paso_se_mueve_al_dia_siguiente(vista):
    momento = vista._momento("00:01")

    assert momento is not None
    assert momento.date().isoformat() == "2026-10-11"
    assert momento.hour == 0
    assert momento.minute == 1
  
@pytest.mark.parametrize("valor", ["abc", "12.5", object()])
def test_id_devuelve_none_para_valores_no_convertibles(valor):
    from quecomo.presentacion.vista import _id

    assert _id(valor) is None

def test_buscar_sin_resultados(vista):
    tabla, resumen = vista.buscar(
        "restaurante_que_no_existe_987",
        TODAS,
        0,
        "Centro",
        15,
        HORARIO_AHORA,
        TODAS,
        0,
        False,
        "Mejor ranking",
    )

    assert tabla.empty
    assert "No hay restaurantes que cumplan todos los criterios" in resumen

def test_lineas_evaluaciones_sin_evaluaciones(vista):
    restaurante = vista.app.restaurantes.obtener(1)

    evaluaciones = vista.app.evaluaciones.obtener_por_restaurante(
        restaurante.id
    )
    evaluaciones_originales = evaluaciones

def test_comparar_cuando_busqueda_no_devuelve_resultados(vista, monkeypatch):
    monkeypatch.setattr(
        vista.app.busqueda,
        "comparar",
        lambda ids, punto: [],
    )

    mensaje, tabla = vista.comparar([1, 2], "Centro")

    assert mensaje == "No hay restaurantes disponibles para comparar."
    assert tabla.empty

def test_tabla_transacciones_incluye_cliente(vista):
    transacciones = vista.app.transacciones.listar_por_usuario(1)

    tabla = vista._tabla_transacciones(transacciones, con_cliente=True)

    assert "Cliente" in tabla.columns
    if transacciones:
        assert len(tabla) == len(transacciones)


def test_mis_transacciones_sin_usuario(vista):
    tabla = vista.mis_transacciones(None)

    assert tabla.empty

def test_opciones_para_evaluar_sin_usuario(vista):
    assert vista.opciones_para_evaluar(None) == []

def test_cancelar_transaccion_desde_vista(vista):
    mensaje = vista.cancelar_transaccion(1, 6)

    assert mensaje.startswith("✅")
    assert "cancelado" in mensaje.lower()
    
    from quecomo.dominio.excepciones import (
    EvaluacionNoPermitida,
    MotivoRechazo,
)

def test_mensaje_rechazo_para_error_que_no_es_evaluacion(vista):
    error = ValueError("Error de prueba")

    assert vista._mensaje_rechazo(error, 1) == "Error de prueba"

def test_mensaje_rechazo_para_transaccion_ajena(vista):
    error = EvaluacionNoPermitida(
        MotivoRechazo.TRANSACCION_AJENA,
        "Mensaje interno de prueba",
    )

    mensaje = vista._mensaje_rechazo(error, 2)

    assert mensaje == "Solo quien hizo el consumo puede evaluarlo."

@pytest.mark.parametrize(
    ("motivo", "esperado"),
    [
        (
            MotivoRechazo.SIN_TRANSACCION,
            "No hay un consumo que respalde la evaluación.",
        ),
        (
            MotivoRechazo.TRANSACCION_CANCELADA,
            "fue cancelado",
        ),
        (
            MotivoRechazo.RESTAURANTE_NO_DISPONIBLE,
            "no está disponible",
        ),
        (
            MotivoRechazo.USUARIO_NO_HABILITADO,
            "Inicia sesión con una cuenta activa",
        ),
    ],
)
def test_mensaje_rechazo_por_motivo(vista, motivo, esperado):
    error = EvaluacionNoPermitida(motivo, "Error de prueba")

    mensaje = vista._mensaje_rechazo(error, 2)

    assert esperado in mensaje

