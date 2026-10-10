"""Fixtures compartidas por las pruebas.

Se usa un reloj fijo para que las pruebas sean deterministas: sábado
10 de octubre de 2026 a las 13:00.
"""

from __future__ import annotations

from datetime import date, datetime, time

import pytest

from quecomo.configuracion import Aplicacion, crear_aplicacion
from quecomo.dominio.entidades import Horario, Restaurante, Ubicacion, Usuario
from quecomo.dominio.estados import Rol

AHORA = datetime(2026, 10, 10, 13, 0)  # sábado


def reloj_fijo() -> datetime:
    return AHORA


@pytest.fixture
def app() -> Aplicacion:
    """Aplicación vacía con un escenario mínimo controlado."""
    aplicacion = crear_aplicacion(datos_demo=False, reloj=reloj_fijo)
    for usuario in [
        Usuario(1, "Ana López", "ana@ejemplo.com", Rol.CLIENTE),
        Usuario(2, "Bruno Méndez", "bruno@ejemplo.com", Rol.CLIENTE),
        Usuario(10, "Héctor Salas", "hector@ejemplo.com", Rol.LOCATARIO),
        Usuario(11, "Elena Torres", "elena@ejemplo.com", Rol.LOCATARIO),
        Usuario(99, "Gabriela Núñez", "admin@ejemplo.com", Rol.ADMINISTRADOR),
    ]:
        aplicacion.usuarios.guardar(usuario)
    aplicacion.restaurantes.guardar(
        Restaurante(
            id=1,
            nombre="Tacos de Prueba",
            descripcion="Restaurante de prueba",
            categoria="Tacos",
            ubicacion=Ubicacion("Calle 1", 29.07, -110.95, "Centro"),
            horario=Horario(frozenset(range(7)), time(9), time(22)),
            formas_pago=frozenset({"Efectivo"}),
            precio_promedio=120,
            fecha_apertura=date(2020, 1, 1),
            locatario_id=10,
        )
    )
    return aplicacion


@pytest.fixture
def app_demo() -> Aplicacion:
    """Aplicación con los datos de demostración."""
    return crear_aplicacion(datos_demo=True, reloj=reloj_fijo)


def transaccion_completada(app: Aplicacion, cliente: int = 1, restaurante: int = 1, importe: int = 200):
    """Recorre el flujo real: cliente registra, locatario confirma y completa."""
    servicio = app.servicio_transacciones
    t = servicio.registrar(cliente, restaurante, importe)
    locatario = app.restaurantes.obtener(restaurante).locatario_id
    servicio.confirmar(locatario, t.id)
    servicio.completar(locatario, t.id)
    return t
