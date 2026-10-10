"""Pruebas de administración de restaurantes y moderación (HU-09, HU-10, HU-11)."""

from datetime import date

import pytest

from quecomo.aplicacion.servicio_restaurantes import DatosRestaurante
from quecomo.dominio.estados import EstadoEvaluacion, EstadoRestaurante
from quecomo.dominio.excepciones import DatosInvalidos, OperacionNoAutorizada

from .conftest import transaccion_completada


def datos(**cambios) -> DatosRestaurante:
    base = dict(
        nombre="Nuevo Lugar",
        descripcion="Comida corrida",
        categoria="Comida mexicana",
        direccion="Calle 2",
        latitud=29.08,
        longitud=-110.96,
        zona="Centro",
        dias=[0, 1, 2, 3, 4],
        apertura="08:00",
        cierre="17:00",
        formas_pago=["Efectivo"],
        precio_promedio=95,
        fecha_apertura="2024-05-01",
    )
    base.update(cambios)
    return DatosRestaurante(**base)


def test_hu09_locatario_registra_restaurante(app):
    r = app.servicio_restaurantes.registrar(11, datos())
    assert r.locatario_id == 11 and r.esta_disponible()
    assert r.fecha_apertura == date(2024, 5, 1)
    assert [x.id for x in app.servicio_restaurantes.mis_restaurantes(11)] == [r.id]


def test_cliente_no_registra_restaurantes(app):
    with pytest.raises(OperacionNoAutorizada):
        app.servicio_restaurantes.registrar(1, datos())


@pytest.mark.parametrize(
    "cambio",
    [
        {"nombre": ""},
        {"formas_pago": []},
        {"formas_pago": ["Efectivo", "Transferencia"]},  # RN-07: sin pagos en línea
        {"formas_pago": ["Pago en línea"]},
        {"dias": []},
        {"apertura": "8am"},
        {"precio_promedio": 0},
        {"fecha_apertura": "01/05/2024"},
        {"latitud": "abc"},
    ],
)
def test_validaciones_de_registro(app, cambio):
    with pytest.raises(DatosInvalidos):
        app.servicio_restaurantes.registrar(11, datos(**cambio))


def test_hu10_actualizar_conserva_menu_y_promociones(app):
    app.servicio_restaurantes.agregar_producto(10, 1, "Taco", 30)
    actualizado = app.servicio_restaurantes.actualizar(10, 1, datos(nombre="Tacos Renovados"))
    assert actualizado.nombre == "Tacos Renovados"
    assert [p.nombre for p in actualizado.productos()] == ["Taco"]


def test_actualizacion_invalida_no_modifica_el_original(app):
    with pytest.raises(DatosInvalidos):
        app.servicio_restaurantes.actualizar(10, 1, datos(nombre=""))
    assert app.restaurantes.obtener(1).nombre == "Tacos de Prueba"


def test_solo_el_dueno_actualiza(app):
    with pytest.raises(OperacionNoAutorizada):
        app.servicio_restaurantes.actualizar(11, 1, datos())


def test_productos_y_promociones(app):
    app.servicio_restaurantes.agregar_producto(10, 1, "Quesadilla", 60, "De harina")
    with pytest.raises(DatosInvalidos):
        app.servicio_restaurantes.agregar_producto(10, 1, "quesadilla", 70)
    promo = app.servicio_restaurantes.agregar_promocion(10, 1, "2x1", "2026-10-01", "2026-10-31")
    assert promo.esta_vigente(date(2026, 10, 10))
    with pytest.raises(DatosInvalidos):
        app.servicio_restaurantes.agregar_promocion(10, 1, "Al revés", "2026-10-31", "2026-10-01")


def test_hu11_locatario_consulta_evaluaciones_recibidas(app):
    t = transaccion_completada(app)
    app.controlador_evaluacion.registrar_evaluacion(1, t.id, 4, "Rico y a buen precio.")
    recibidas = app.servicio_restaurantes.evaluaciones_recibidas(10, 1)
    assert [e.calificacion for e in recibidas] == [4]
    with pytest.raises(OperacionNoAutorizada):
        app.servicio_restaurantes.evaluaciones_recibidas(11, 1)


class TestAdministrador:
    def test_suspender_y_activar(self, app):
        app.servicio_restaurantes.cambiar_estado(99, 1, EstadoRestaurante.SUSPENDIDO)
        assert not app.restaurantes.obtener(1).esta_disponible()
        app.servicio_restaurantes.cambiar_estado(99, 1, EstadoRestaurante.ACTIVO)
        assert app.restaurantes.obtener(1).esta_disponible()

    def test_locatario_no_puede_suspender(self, app):
        with pytest.raises(OperacionNoAutorizada):
            app.servicio_restaurantes.cambiar_estado(10, 1, EstadoRestaurante.SUSPENDIDO)

    def test_moderacion_requiere_motivo_y_es_reversible(self, app):
        t = transaccion_completada(app)
        e = app.controlador_evaluacion.registrar_evaluacion(1, t.id, 1, "Comentario a moderar.")
        with pytest.raises(DatosInvalidos):
            app.servicio_restaurantes.ocultar_evaluacion(99, e.id, "")
        app.servicio_restaurantes.ocultar_evaluacion(99, e.id, "Lenguaje ofensivo")
        assert e.estado is EstadoEvaluacion.OCULTA
        assert app.ranking.calcular(1).total == 0
        # Ocultar no libera la transacción: sigue sin poder respaldar otra evaluación.
        assert not t.puede_evaluarse()
        app.servicio_restaurantes.restaurar_evaluacion(99, e.id)
        assert app.ranking.calcular(1).total == 1

    def test_cliente_no_modera(self, app):
        with pytest.raises(OperacionNoAutorizada):
            app.servicio_restaurantes.todas_las_evaluaciones(1)
