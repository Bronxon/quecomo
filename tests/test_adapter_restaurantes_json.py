
import json
from datetime import date, time
from decimal import Decimal
from pathlib import Path

import pytest

from quecomo.dominio.entidades import Restaurante, Ubicacion, Horario
from quecomo.dominio.estados import EstadoRestaurante
from quecomo.infraestructura.adapter_restaurantes_json import (
    AdapterRestaurantesJSON,
    ErrorFormatoRestaurantes,
)


FIXTURE = Path(__file__).parent / "fixtures" / "restaurantes_externos.json"


def test_convertir_registro_json_a_restaurante():
    registro = {
        "id": 901,
        "nombre": "Café Adaptador",
        "descripcion": "Cafetería de prueba",
        "categoria": "Cafetería",
        "ubicacion": {
            "direccion": "Blvd. Ejemplo 100",
            "latitud": 29.0729,
            "longitud": -110.9559,
            "zona": "Centro",
        },
        "horario": {
            "dias": [0, 1, 2, 3, 4, 5],
            "apertura": "08:00",
            "cierre": "22:00",
        },
        "formas_pago": ["Efectivo", "Tarjeta de débito"],
        "precio_promedio": "125.50",
        "fecha_apertura": "2024-03-15",
        "locatario_id": 901,
        "estado": "ACTIVO",
    }

    restaurante = AdapterRestaurantesJSON.convertir(registro)

    assert isinstance(restaurante, Restaurante)
    assert restaurante.id == 901
    assert restaurante.nombre == "Café Adaptador"
    assert restaurante.ubicacion == Ubicacion(
        "Blvd. Ejemplo 100", 29.0729, -110.9559, "Centro"
    )
    assert restaurante.horario == Horario(
        frozenset({0, 1, 2, 3, 4, 5}),
        time(8, 0),
        time(22, 0),
    )
    assert restaurante.formas_pago == frozenset({"Efectivo", "Tarjeta de débito"})
    assert restaurante.precio_promedio == Decimal("125.50")
    assert restaurante.fecha_apertura == date(2024, 3, 15)
    assert restaurante.estado is EstadoRestaurante.ACTIVO


def test_estado_activo_es_predeterminado():
    registro = {
        "id": 902,
        "nombre": "Restaurante de prueba",
        "descripcion": "Descripción",
        "categoria": "Mexicana",
        "ubicacion": {
            "direccion": "Calle de prueba",
            "latitud": 29.0,
            "longitud": -110.0,
        },
        "horario": {
            "dias": [0, 1],
            "apertura": "09:00",
            "cierre": "18:00",
        },
        "formas_pago": ["Efectivo"],
        "precio_promedio": "100",
        "fecha_apertura": "2020-01-01",
        "locatario_id": 902,
    }

    restaurante = AdapterRestaurantesJSON.convertir(registro)

    assert restaurante.estado is EstadoRestaurante.ACTIVO
    assert restaurante.ubicacion.zona == ""


def test_rechaza_registro_incompleto():
    with pytest.raises(ErrorFormatoRestaurantes):
        AdapterRestaurantesJSON.convertir({"id": 1})


def test_rechaza_estado_desconocido():
    registro = {
        "id": 903,
        "nombre": "Prueba",
        "descripcion": "Descripción",
        "categoria": "Mexicana",
        "ubicacion": {
            "direccion": "Calle",
            "latitud": 29.0,
            "longitud": -110.0,
        },
        "horario": {
            "dias": [0],
            "apertura": "09:00",
            "cierre": "18:00",
        },
        "formas_pago": ["Efectivo"],
        "precio_promedio": "100",
        "fecha_apertura": "2020-01-01",
        "locatario_id": 903,
        "estado": "DESCONOCIDO",
    }

    with pytest.raises(ErrorFormatoRestaurantes):
        AdapterRestaurantesJSON.convertir(registro)


def test_carga_archivo_json():
    restaurantes = AdapterRestaurantesJSON.cargar_archivo(FIXTURE)

    assert len(restaurantes) == 1
    assert restaurantes[0].nombre == "Café Adaptador"
    assert restaurantes[0].precio_promedio == Decimal("125.50")


def test_rechaza_json_que_no_es_una_lista(tmp_path):
    archivo = tmp_path / "restaurantes.json"
    archivo.write_text(
        json.dumps({"id": 1}),
        encoding="utf-8",
    )

    with pytest.raises(ErrorFormatoRestaurantes):
        AdapterRestaurantesJSON.cargar_archivo(archivo)


def test_rechaza_archivo_inexistente(tmp_path):
    with pytest.raises(ErrorFormatoRestaurantes):
        AdapterRestaurantesJSON.cargar_archivo(
            tmp_path / "no_existe.json"
        )
