"""Pruebas unitarias de la máquina de estados de Transacción (sección 10.3)."""

from datetime import datetime

import pytest

from quecomo.dominio.entidades import Transaccion
from quecomo.dominio.estados import EstadoTransaccion
from quecomo.dominio.excepciones import (
    DatosInvalidos,
    EvaluacionNoPermitida,
    MotivoRechazo,
    TransicionInvalida,
)

T0 = datetime(2026, 10, 1, 14, 0)


def nueva(importe=150) -> Transaccion:
    return Transaccion(1, usuario_id=1, restaurante_id=1, importe=importe, fecha=T0)


def completada() -> Transaccion:
    t = nueva()
    t.enviar(T0)
    t.confirmar(T0)
    t.completar(T0)
    return t


class TestCicloDeVida:
    def test_inicia_en_iniciada(self):
        assert nueva().estado is EstadoTransaccion.INICIADA

    def test_flujo_feliz_hasta_completada(self):
        t = completada()
        assert t.estado is EstadoTransaccion.COMPLETADA
        assert [c.estado for c in t.historial] == [
            EstadoTransaccion.INICIADA,
            EstadoTransaccion.PENDIENTE,
            EstadoTransaccion.CONFIRMADA,
            EstadoTransaccion.COMPLETADA,
        ]

    @pytest.mark.parametrize("pasos", [["enviar"], ["enviar", "confirmar"]])
    def test_cancelar_desde_pendiente_o_confirmada(self, pasos):
        t = nueva()
        for paso in pasos:
            getattr(t, paso)(T0)
        t.cancelar(T0, motivo="Cliente se retiró")
        assert t.estado is EstadoTransaccion.CANCELADA
        assert t.historial[-1].nota == "Cliente se retiró"

    def test_cancelada_a_completada_es_invalida(self):
        """La sección 10.3 lo señala explícitamente."""
        t = nueva()
        t.enviar(T0)
        t.cancelar(T0)
        with pytest.raises(TransicionInvalida):
            t.completar(T0)

    @pytest.mark.parametrize(
        "operacion", ["confirmar", "completar", "cancelar"]
    )
    def test_desde_iniciada_solo_se_puede_enviar(self, operacion):
        with pytest.raises(TransicionInvalida):
            getattr(nueva(), operacion)(T0)

    def test_no_se_puede_saltar_la_confirmacion(self):
        t = nueva()
        t.enviar(T0)
        with pytest.raises(TransicionInvalida):
            t.completar(T0)

    def test_completada_es_final(self):
        t = completada()
        with pytest.raises(TransicionInvalida):
            t.cancelar(T0)
        assert t.estado.es_final

    def test_el_estado_no_se_asigna_directamente(self):
        """CA-08: el estado solo cambia mediante operaciones controladas."""
        t = nueva()
        with pytest.raises(AttributeError):
            t.estado = EstadoTransaccion.COMPLETADA  # type: ignore[misc]


class TestImporte:
    @pytest.mark.parametrize("importe", [0, -10, "abc", None])
    def test_importe_invalido(self, importe):
        with pytest.raises(DatosInvalidos):
            nueva(importe)

    def test_importe_se_redondea_a_centavos(self):
        assert str(nueva("99.999").importe) == "100.00"


class TestPuedeEvaluarse:
    """Guarda principal: [estado == COMPLETADA AND noExisteEvaluacion]."""

    @pytest.mark.parametrize("pasos", [[], ["enviar"], ["enviar", "confirmar"]])
    def test_no_completada_no_habilita(self, pasos):
        t = nueva()
        for paso in pasos:
            getattr(t, paso)(T0)
        assert not t.puede_evaluarse()

    def test_cancelada_no_habilita(self):
        """RN-05."""
        t = nueva()
        t.enviar(T0)
        t.cancelar(T0)
        assert not t.puede_evaluarse()
        with pytest.raises(EvaluacionNoPermitida) as error:
            t.verificar_evaluable_por(1)
        assert error.value.motivo is MotivoRechazo.TRANSACCION_CANCELADA

    def test_completada_sin_evaluacion_habilita(self):
        assert completada().puede_evaluarse()

    def test_ya_evaluada_no_habilita_otra(self):
        """RN-06."""
        t = completada()
        t.vincular_evaluacion(50)
        assert not t.puede_evaluarse()
        with pytest.raises(EvaluacionNoPermitida):
            t.vincular_evaluacion(51)
        assert t.evaluacion_id == 50

    def test_solo_el_dueno_puede_evaluar(self):
        """RN-01: la transacción debe ser entre ESE usuario y el restaurante."""
        with pytest.raises(EvaluacionNoPermitida) as error:
            completada().verificar_evaluable_por(usuario_id=2)
        assert error.value.motivo is MotivoRechazo.TRANSACCION_AJENA
