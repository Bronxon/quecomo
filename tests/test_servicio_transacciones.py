"""Pruebas de registro y control de transacciones (HU-06, CA-03, CA-08)."""

import pytest

from quecomo.dominio.estados import EstadoRestaurante, EstadoTransaccion
from quecomo.dominio.excepciones import (
    DatosInvalidos,
    EntidadNoEncontrada,
    OperacionNoAutorizada,
    TransicionInvalida,
)


def test_ca03_registrar_transaccion(app):
    t = app.servicio_transacciones.registrar(1, 1, "250.50")
    assert (t.usuario_id, t.restaurante_id, str(t.importe)) == (1, 1, "250.50")
    assert t.estado is EstadoTransaccion.PENDIENTE
    assert app.transacciones.obtener(t.id) is t


def test_solo_clientes_registran_transacciones(app):
    with pytest.raises(OperacionNoAutorizada):
        app.servicio_transacciones.registrar(10, 1, 100)


def test_no_se_registra_en_restaurante_suspendido(app):
    app.restaurantes.obtener(1).estado = EstadoRestaurante.SUSPENDIDO
    with pytest.raises(DatosInvalidos):
        app.servicio_transacciones.registrar(1, 1, 100)


def test_restaurante_inexistente(app):
    with pytest.raises(EntidadNoEncontrada):
        app.servicio_transacciones.registrar(1, 999, 100)


def test_importe_maximo(app):
    with pytest.raises(DatosInvalidos):
        app.servicio_transacciones.registrar(1, 1, 1_000_000)


class TestCA08ControlDeEstados:
    """El cliente no puede mover su transacción a COMPLETADA para habilitarse."""

    def test_cliente_no_puede_confirmar_ni_completar(self, app):
        t = app.servicio_transacciones.registrar(1, 1, 100)
        with pytest.raises(OperacionNoAutorizada):
            app.servicio_transacciones.confirmar(1, t.id)
        app.servicio_transacciones.confirmar(10, t.id)
        with pytest.raises(OperacionNoAutorizada):
            app.servicio_transacciones.completar(1, t.id)
        assert t.estado is EstadoTransaccion.CONFIRMADA

    def test_otro_locatario_no_puede_gestionar(self, app):
        t = app.servicio_transacciones.registrar(1, 1, 100)
        with pytest.raises(OperacionNoAutorizada):
            app.servicio_transacciones.confirmar(11, t.id)

    def test_administrador_no_fabrica_evidencia(self, app):
        t = app.servicio_transacciones.registrar(1, 1, 100)
        with pytest.raises(OperacionNoAutorizada):
            app.servicio_transacciones.confirmar(99, t.id)

    def test_locatario_dueno_completa(self, app):
        t = app.servicio_transacciones.registrar(1, 1, 100)
        app.servicio_transacciones.confirmar(10, t.id)
        app.servicio_transacciones.completar(10, t.id)
        assert t.estado is EstadoTransaccion.COMPLETADA
        assert t.historial[-1].actor_id == 10

    def test_cliente_cancela_solo_las_suyas(self, app):
        t = app.servicio_transacciones.registrar(1, 1, 100)
        with pytest.raises(OperacionNoAutorizada):
            app.servicio_transacciones.cancelar(2, t.id)
        app.servicio_transacciones.cancelar(1, t.id)
        assert t.estado is EstadoTransaccion.CANCELADA

    def test_no_se_completa_una_cancelada(self, app):
        t = app.servicio_transacciones.registrar(1, 1, 100)
        app.servicio_transacciones.cancelar(10, t.id)
        with pytest.raises(TransicionInvalida):
            app.servicio_transacciones.confirmar(10, t.id)


def test_listados(app):
    t1 = app.servicio_transacciones.registrar(1, 1, 100)
    t2 = app.servicio_transacciones.registrar(2, 1, 100)
    assert [t.id for t in app.servicio_transacciones.listar_de_usuario(1)] == [t1.id]
    assert {t.id for t in app.servicio_transacciones.listar_de_restaurante(10, 1)} == {t1.id, t2.id}
    with pytest.raises(OperacionNoAutorizada):
        app.servicio_transacciones.listar_de_restaurante(11, 1)
