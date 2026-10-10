"""Pruebas de integración del caso de uso CU-01 y sus extensiones.

Cada prueba indica el criterio de aceptación (CA) o la regla (RN) que verifica.
"""

import threading
from datetime import datetime

import pytest

from quecomo.dominio.entidades import Evaluacion, Transaccion
from quecomo.dominio.estados import EstadoRestaurante, EstadoUsuario
from quecomo.dominio.excepciones import (
    DatosInvalidos,
    EvaluacionNoPermitida,
    MotivoRechazo,
)

from .conftest import transaccion_completada

COMENTARIO = "Muy buena comida y atención amable."


def test_ca05_ca06_flujo_principal(app):
    """CA-05 y CA-06: transacción completada → evaluación vinculada a usuario, restaurante y transacción."""
    t = transaccion_completada(app)
    assert app.controlador_evaluacion.solicitar_evaluacion(1, t.id) is t

    e = app.controlador_evaluacion.registrar_evaluacion(1, t.id, 5, COMENTARIO)

    assert (e.usuario_id, e.restaurante_id, e.transaccion_id) == (1, 1, t.id)
    assert app.evaluaciones.obtener(e.id) is e
    assert app.transacciones.obtener(t.id).evaluacion_id == e.id
    assert app.ranking.calcular(1).promedio == 5


def test_ca07_sin_transaccion_es_rechazada(app):
    """CA-07 / extensión «No existe transacción»."""
    with pytest.raises(EvaluacionNoPermitida) as error:
        app.controlador_evaluacion.registrar_evaluacion(1, None, 5, COMENTARIO)
    assert error.value.motivo is MotivoRechazo.SIN_TRANSACCION
    with pytest.raises(EvaluacionNoPermitida):
        app.controlador_evaluacion.registrar_evaluacion(1, 12345, 5, COMENTARIO)
    assert app.evaluaciones.listar() == []


@pytest.mark.parametrize("pasos", [[], ["confirmar"]])
def test_ca04_transaccion_incompleta_no_habilita(app, pasos):
    """CA-04: PENDIENTE o CONFIRMADA no habilitan la evaluación."""
    t = app.servicio_transacciones.registrar(1, 1, 200)
    for paso in pasos:
        getattr(app.servicio_transacciones, paso)(10, t.id)
    with pytest.raises(EvaluacionNoPermitida) as error:
        app.controlador_evaluacion.registrar_evaluacion(1, t.id, 4, COMENTARIO)
    assert error.value.motivo is MotivoRechazo.TRANSACCION_NO_COMPLETADA


def test_ca04_rn05_transaccion_cancelada_no_habilita(app):
    t = app.servicio_transacciones.registrar(1, 1, 200)
    app.servicio_transacciones.cancelar(1, t.id)
    with pytest.raises(EvaluacionNoPermitida) as error:
        app.controlador_evaluacion.solicitar_evaluacion(1, t.id)
    assert error.value.motivo is MotivoRechazo.TRANSACCION_CANCELADA


def test_rn06_una_sola_evaluacion_por_transaccion(app):
    t = transaccion_completada(app)
    app.controlador_evaluacion.registrar_evaluacion(1, t.id, 5, COMENTARIO)
    with pytest.raises(EvaluacionNoPermitida) as error:
        app.controlador_evaluacion.registrar_evaluacion(1, t.id, 1, "Intento de segunda evaluación")
    assert error.value.motivo is MotivoRechazo.TRANSACCION_YA_EVALUADA
    assert len(app.evaluaciones.listar()) == 1


def test_rn01_no_se_puede_usar_la_transaccion_de_otro(app):
    t = transaccion_completada(app, cliente=1)
    with pytest.raises(EvaluacionNoPermitida) as error:
        app.controlador_evaluacion.registrar_evaluacion(2, t.id, 1, COMENTARIO)
    assert error.value.motivo is MotivoRechazo.TRANSACCION_AJENA


def test_rn04_evaluacion_no_puede_crearse_sin_transaccion_valida():
    """RN-04: Evaluacion.crear exige una transacción evaluable; nunca al revés."""
    t = Transaccion(1, 1, 1, 100, datetime(2026, 1, 1))
    with pytest.raises(EvaluacionNoPermitida):
        Evaluacion.crear(1, t, 5, COMENTARIO, datetime(2026, 1, 1))


def test_extension_restaurante_no_disponible(app):
    t = transaccion_completada(app)
    app.restaurantes.obtener(1).estado = EstadoRestaurante.SUSPENDIDO
    with pytest.raises(EvaluacionNoPermitida) as error:
        app.controlador_evaluacion.registrar_evaluacion(1, t.id, 5, COMENTARIO)
    assert error.value.motivo is MotivoRechazo.RESTAURANTE_NO_DISPONIBLE


def test_usuario_bloqueado_no_puede_evaluar(app):
    t = transaccion_completada(app)
    app.usuarios.obtener(1).estado = EstadoUsuario.BLOQUEADO
    with pytest.raises(EvaluacionNoPermitida) as error:
        app.controlador_evaluacion.registrar_evaluacion(1, t.id, 5, COMENTARIO)
    assert error.value.motivo is MotivoRechazo.USUARIO_NO_HABILITADO


@pytest.mark.parametrize(
    "calificacion, comentario",
    [(None, COMENTARIO), (0, COMENTARIO), (6, COMENTARIO), (4.5, COMENTARIO), ("x", COMENTARIO), (4, "corto"), (4, "")],
)
def test_extension_evaluacion_incompleta(app, calificacion, comentario):
    """Extensión «Evaluación incompleta»: no se registra y la transacción sigue disponible."""
    t = transaccion_completada(app)
    with pytest.raises(DatosInvalidos):
        app.controlador_evaluacion.registrar_evaluacion(1, t.id, calificacion, comentario)
    assert app.evaluaciones.listar() == []
    assert t.puede_evaluarse()


def test_transacciones_evaluables(app):
    completa = transaccion_completada(app)
    app.servicio_transacciones.registrar(1, 1, 300)  # pendiente
    evaluables = app.controlador_evaluacion.transacciones_evaluables(1)
    assert [t.id for t in evaluables] == [completa.id]


def test_concurrencia_no_duplica_evaluaciones(app):
    """Dos solicitudes simultáneas sobre la misma transacción: solo una gana (RN-06)."""
    t = transaccion_completada(app)
    resultados: list[str] = []

    def intentar():
        try:
            app.controlador_evaluacion.registrar_evaluacion(1, t.id, 5, COMENTARIO)
            resultados.append("ok")
        except EvaluacionNoPermitida:
            resultados.append("rechazada")

    hilos = [threading.Thread(target=intentar) for _ in range(8)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    assert resultados.count("ok") == 1
    assert len(app.evaluaciones.listar()) == 1


def test_repositorio_rechaza_duplicado_como_restriccion_unica(app):
    """Defensa en profundidad: aunque se salte el controlador, el repositorio
    no admite dos evaluaciones para la misma transacción."""
    t = transaccion_completada(app)
    e1 = Evaluacion.crear(1, t, 5, COMENTARIO, datetime(2026, 1, 1))
    app.evaluaciones.guardar(e1)
    e2 = Evaluacion(2, 1, 1, t.id, 3, COMENTARIO, datetime(2026, 1, 1))
    with pytest.raises(DatosInvalidos):
        app.evaluaciones.guardar(e2)
