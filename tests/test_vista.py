"""Pruebas de la capa de presentación (sin levantar el servidor)."""

import gradio as gr
import pytest

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
