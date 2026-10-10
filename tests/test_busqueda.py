"""Pruebas de búsqueda, filtros, comparación y ranking (HU-01 a HU-05, CA-01, CA-02)."""

from datetime import datetime, time

import pytest

from quecomo.aplicacion.servicio_busqueda import CriteriosBusqueda, Orden
from quecomo.dominio.entidades import Horario, Ubicacion
from quecomo.dominio.excepciones import DatosInvalidos


def nombres(resultados):
    return [r.restaurante.nombre for r in resultados]


def test_ca01_consultar_restaurantes_disponibles(app_demo):
    assert len(app_demo.busqueda.buscar(CriteriosBusqueda())) == 8


def test_restaurante_suspendido_no_aparece(app_demo):
    from quecomo.dominio.estados import EstadoRestaurante

    app_demo.restaurantes.obtener(2).estado = EstadoRestaurante.SUSPENDIDO
    assert "Tacos La Lumbre" not in nombres(app_demo.busqueda.buscar(CriteriosBusqueda()))


class TestCA02Filtros:
    def test_texto_sin_acentos_y_en_menu(self, app_demo):
        assert nombres(app_demo.busqueda.buscar(CriteriosBusqueda(texto="cafe"))) == ["Café Desierto"]
        # «ramen» solo aparece en el menú de Sushi Kaze
        assert nombres(app_demo.busqueda.buscar(CriteriosBusqueda(texto="RAMEN"))) == ["Sushi Kaze"]

    def test_categoria(self, app_demo):
        assert nombres(app_demo.busqueda.buscar(CriteriosBusqueda(categoria="Mariscos"))) == [
            "Mariscos El Faro Azul"
        ]

    def test_precio_maximo(self, app_demo):
        resultados = app_demo.busqueda.buscar(CriteriosBusqueda(precio_maximo=120))
        assert all(r.restaurante.precio_promedio <= 120 for r in resultados)
        assert len(resultados) == 3

    def test_distancia_maxima(self, app_demo):
        centro = app_demo.punto("Centro")
        resultados = app_demo.busqueda.buscar(CriteriosBusqueda(punto=centro, distancia_maxima_km=1))
        assert resultados and all(r.distancia_km <= 1 for r in resultados)

    def test_forma_de_pago(self, app_demo):
        resultados = app_demo.busqueda.buscar(CriteriosBusqueda(forma_pago="Tarjeta de crédito"))
        assert resultados and all("Tarjeta de crédito" in r.restaurante.formas_pago for r in resultados)
        assert "Antojitos Doña Chayo" not in nombres(resultados)  # solo efectivo

    def test_rn07_no_hay_pagos_en_linea(self, app_demo):
        """RN-07: ni el catálogo de filtros ni los restaurantes ofrecen pagos en línea."""
        assert app_demo.busqueda.formas_pago() == ["Efectivo", "Tarjeta de crédito", "Tarjeta de débito"]

    def test_horario(self, app_demo):
        # Sábado 13:00: Antojitos (L-S 8-16) abierto; Tacos La Lumbre (18-02) cerrado.
        abiertos = nombres(app_demo.busqueda.buscar(CriteriosBusqueda(abierto_en=datetime(2026, 10, 10, 13, 0))))
        assert "Antojitos Doña Chayo" in abiertos
        assert "Tacos La Lumbre" not in abiertos

    def test_calificacion_minima_excluye_sin_evaluaciones(self, app_demo):
        resultados = app_demo.busqueda.buscar(CriteriosBusqueda(calificacion_minima=4))
        assert all(r.ranking.promedio >= 4 for r in resultados)
        assert "Café Desierto" not in nombres(resultados)

    def test_solo_con_promocion(self, app_demo):
        resultados = app_demo.busqueda.buscar(CriteriosBusqueda(solo_con_promocion=True))
        assert resultados and all(r.promociones_vigentes > 0 for r in resultados)
        # La promoción de Café Desierto ya venció
        assert "Café Desierto" not in nombres(resultados)

    def test_filtros_combinados_sin_resultados(self, app_demo):
        criterios = CriteriosBusqueda(categoria="Sushi", precio_maximo=100)
        assert app_demo.busqueda.buscar(criterios) == []


class TestOrden:
    def test_por_precio(self, app_demo):
        precios = [r.restaurante.precio_promedio for r in app_demo.busqueda.buscar(CriteriosBusqueda(orden=Orden.PRECIO))]
        assert precios == sorted(precios)

    def test_por_distancia(self, app_demo):
        criterios = CriteriosBusqueda(punto=app_demo.punto("Zona Sur"), orden=Orden.DISTANCIA)
        distancias = [r.distancia_km for r in app_demo.busqueda.buscar(criterios)]
        assert distancias == sorted(distancias)

    def test_ranking_sin_evaluaciones_al_final(self, app_demo):
        assert nombres(app_demo.busqueda.buscar(CriteriosBusqueda()))[-1] == "Café Desierto"

    def test_ranking_ponderado_favorece_volumen(self, app_demo):
        """4.5 con 2 evaluaciones supera a 5.0 con 1 evaluación."""
        orden = nombres(app_demo.busqueda.buscar(CriteriosBusqueda()))
        assert orden.index("Antojitos Doña Chayo") < orden.index("Verde Raíz")


class TestComparar:
    def test_comparar_dos_o_tres(self, app_demo):
        assert len(app_demo.busqueda.comparar([1, 2, 3])) == 3

    @pytest.mark.parametrize("ids", [[], [1], [1, 1], [1, 2, 3, 4]])
    def test_limites(self, app_demo, ids):
        with pytest.raises(DatosInvalidos):
            app_demo.busqueda.comparar(ids)


class TestRanking:
    def test_solo_evaluaciones_publicadas(self, app_demo):
        antes = app_demo.ranking.calcular(1)
        evaluacion = app_demo.evaluaciones.obtener_por_restaurante(1)[0]
        evaluacion.ocultar("Contenido inapropiado")
        despues = app_demo.ranking.calcular(1)
        assert despues.total == antes.total - 1

    def test_sin_evaluaciones(self, app):
        ranking = app.ranking.calcular(1)
        assert ranking.promedio is None and ranking.texto() == "Sin evaluaciones"


class TestObjetosDeValor:
    def test_horario_que_cruza_medianoche(self):
        h = Horario(frozenset({4}), time(18), time(2))  # viernes 18:00–02:00
        assert h.esta_abierto(datetime(2026, 10, 9, 23, 0))  # viernes 23:00
        assert h.esta_abierto(datetime(2026, 10, 10, 1, 30))  # sábado 01:30 (tramo del viernes)
        assert not h.esta_abierto(datetime(2026, 10, 10, 3, 0))
        assert not h.esta_abierto(datetime(2026, 10, 10, 19, 0))  # sábado no abre

    def test_horario_describir(self):
        assert Horario(frozenset(range(7)), time(9), time(18)).describir() == "Todos los días, 09:00–18:00"
        assert Horario(frozenset(range(6)), time(9), time(18)).describir().startswith("Lun a Sáb")

    def test_distancia_haversine(self):
        a = Ubicacion("A", 29.0729, -110.9559)
        assert a.distancia_km(29.0729, -110.9559) == pytest.approx(0)
        # ~1 grado de latitud ≈ 111 km
        assert a.distancia_km(30.0729, -110.9559) == pytest.approx(111.2, abs=0.5)

    def test_coordenadas_invalidas(self):
        with pytest.raises(DatosInvalidos):
            Ubicacion("X", 120, 0)
