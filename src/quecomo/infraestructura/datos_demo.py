"""Datos de demostración.

⚠️ Todos los restaurantes, personas, coordenadas, precios y evaluaciones son
**ficticios** y existen solo para mostrar el funcionamiento del MVP.
Cualquier parecido con establecimientos reales es coincidencia.

Los datos se crean usando las mismas operaciones del dominio (``enviar``,
``confirmar``, ``completar``, ``Evaluacion.crear``...), de modo que la
semilla nunca rompe las reglas de negocio.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from ..dominio.entidades import (
    FORMAS_PAGO_PERMITIDAS,
    Evaluacion,
    Horario,
    Menu,
    Producto,
    Promocion,
    Restaurante,
    Transaccion,
    Ubicacion,
    Usuario,
)
from ..dominio.estados import EstadoTransaccion, Rol
from ..dominio.repositorios import (
    IRepositorioEvaluaciones,
    IRepositorioRestaurantes,
    IRepositorioTransacciones,
    IRepositorioUsuarios,
)

TODOS = frozenset(range(7))
# Solo pagos en el local: ¿Qué Como? no maneja pagos en línea (RN-07).
EFECTIVO, DEBITO, CREDITO = FORMAS_PAGO_PERMITIDAS

# (nombre, latitud, longitud) — coordenadas de demostración.
PUNTOS_REFERENCIA: list[tuple[str, float, float]] = [
    ("Centro", 29.0729, -110.9559),
    ("Zona Norte", 29.1100, -110.9600),
    ("Zona Sur", 29.0300, -110.9500),
    ("Zona Universitaria", 29.0830, -110.9640),
    ("Zona Poniente", 29.0850, -111.0000),
]


def _usuarios() -> list[Usuario]:
    return [
        Usuario(1, "Ana López", "ana@ejemplo.com", Rol.CLIENTE),
        Usuario(2, "Bruno Méndez", "bruno@ejemplo.com", Rol.CLIENTE),
        Usuario(3, "Carla Ruiz", "carla@ejemplo.com", Rol.CLIENTE),
        Usuario(4, "Héctor Salas", "hector@ejemplo.com", Rol.LOCATARIO),
        Usuario(5, "Elena Torres", "elena@ejemplo.com", Rol.LOCATARIO),
        Usuario(6, "Fernando Ibarra", "fernando@ejemplo.com", Rol.LOCATARIO),
        Usuario(7, "Gabriela Núñez", "admin@ejemplo.com", Rol.ADMINISTRADOR),
    ]


def _menu(*productos: tuple[str, float, str]) -> list[Menu]:
    return [
        Menu(
            id=1,
            nombre="Menú principal",
            productos=[
                Producto(id=i, nombre=n, precio=p, descripcion=d)
                for i, (n, p, d) in enumerate(productos, start=1)
            ],
        )
    ]


def _restaurantes(hoy: date) -> list[Restaurante]:
    vigente = (hoy - timedelta(days=5), hoy + timedelta(days=25))
    vencida = (hoy - timedelta(days=60), hoy - timedelta(days=30))

    def h(dias: frozenset[int], abre: str, cierra: str) -> Horario:
        return Horario(dias, time.fromisoformat(abre), time.fromisoformat(cierra))

    return [
        Restaurante(
            id=1,
            nombre="Mariscos El Faro Azul",
            descripcion="Cocteles, aguachiles y pescado zarandeado al estilo de la costa.",
            categoria="Mariscos",
            ubicacion=Ubicacion("Av. del Mar 120", 29.0805, -110.9702, "Zona Universitaria"),
            horario=h(TODOS, "11:00", "19:00"),
            formas_pago=frozenset({EFECTIVO, DEBITO, CREDITO}),
            precio_promedio=280,
            fecha_apertura=date(2012, 4, 15),
            locatario_id=4,
            menus=_menu(
                ("Aguachile verde", 230, "Camarón, pepino y cebolla morada"),
                ("Coctel campechano", 210, "Camarón, pulpo y ostión"),
                ("Pescado zarandeado (kg)", 420, "Para compartir"),
                ("Tostada de ceviche", 75, "Pescado curtido en limón"),
            ),
            promociones=[Promocion(1, "2×1 en tostadas los martes", *vigente, "Solo en consumo en el local")],
        ),
        Restaurante(
            id=2,
            nombre="Tacos La Lumbre",
            descripcion="Tacos de carne asada y tripitas al carbón, abierto hasta la madrugada.",
            categoria="Tacos",
            ubicacion=Ubicacion("Calle Fogón 45", 29.0741, -110.9530, "Centro"),
            horario=h(frozenset({1, 2, 3, 4, 5, 6}), "18:00", "02:00"),
            formas_pago=frozenset({EFECTIVO}),
            precio_promedio=120,
            fecha_apertura=date(2018, 9, 1),
            locatario_id=4,
            menus=_menu(
                ("Taco de carne asada", 35, "Tortilla de maíz o harina"),
                ("Taco de tripitas", 38, "Bien doraditas"),
                ("Quesadilla con carne", 70, "Queso regional"),
                ("Agua fresca", 30, "Horchata o jamaica"),
            ),
        ),
        Restaurante(
            id=3,
            nombre="Café Desierto",
            descripcion="Café de especialidad, desayunos y repostería artesanal.",
            categoria="Cafetería",
            ubicacion=Ubicacion("Blvd. Sahuaro 300", 29.0868, -110.9615, "Zona Universitaria"),
            horario=h(frozenset({0, 1, 2, 3, 4, 5}), "07:00", "21:00"),
            formas_pago=frozenset({EFECTIVO, DEBITO, CREDITO}),
            precio_promedio=110,
            fecha_apertura=date(2021, 2, 10),
            locatario_id=4,
            menus=_menu(
                ("Americano", 45, "Grano de altura"),
                ("Chilaquiles verdes", 120, "Con huevo estrellado"),
                ("Pan de elote", 55, "Receta de la casa"),
            ),
            promociones=[Promocion(2, "Café gratis con tu desayuno", *vencida, "Promoción terminada")],
        ),
        Restaurante(
            id=4,
            nombre="Asadero Los Mezquites",
            descripcion="Cortes de res a la leña de mezquite y frijoles charros.",
            categoria="Carne asada",
            ubicacion=Ubicacion("Carretera Norte km 3", 29.1150, -110.9580, "Zona Norte"),
            horario=h(frozenset({2, 3, 4, 5, 6}), "13:00", "23:00"),
            formas_pago=frozenset({EFECTIVO, DEBITO, CREDITO}),
            precio_promedio=350,
            fecha_apertura=date(2009, 11, 20),
            locatario_id=5,
            menus=_menu(
                ("Arrachera 400 g", 340, "Con guarnición"),
                ("Rib eye 500 g", 520, "Término al gusto"),
                ("Frijoles charros", 60, "Porción individual"),
            ),
            promociones=[Promocion(3, "Postre de cortesía en cumpleaños", *vigente, "Presentar identificación")],
        ),
        Restaurante(
            id=5,
            nombre="Sushi Kaze",
            descripcion="Rollos clásicos y de autor, ramen y entradas japonesas.",
            categoria="Sushi",
            ubicacion=Ubicacion("Plaza Oriente local 8", 29.0650, -110.9350, "Centro"),
            horario=h(TODOS, "13:00", "22:30"),
            formas_pago=frozenset({DEBITO, CREDITO}),
            precio_promedio=260,
            fecha_apertura=date(2016, 6, 5),
            locatario_id=5,
            menus=_menu(
                ("Rollo California", 150, "Surimi, pepino y aguacate"),
                ("Ramen de cerdo", 210, "Caldo tonkotsu"),
                ("Edamames", 80, "Con sal de mar"),
            ),
        ),
        Restaurante(
            id=6,
            nombre="Pizzería Brasa Lenta",
            descripcion="Pizza de masa madre horneada en horno de leña.",
            categoria="Pizzería",
            ubicacion=Ubicacion("Calle Olivo 18", 29.0340, -110.9470, "Zona Sur"),
            horario=h(TODOS, "14:00", "23:30"),
            formas_pago=frozenset({EFECTIVO, DEBITO, CREDITO}),
            precio_promedio=220,
            fecha_apertura=date(2019, 3, 12),
            locatario_id=5,
            menus=_menu(
                ("Pizza margarita", 190, "Jitomate, mozzarella y albahaca"),
                ("Pizza de chorizo", 230, "Chorizo artesanal"),
                ("Ensalada de la casa", 120, "Hojas verdes y vinagreta"),
            ),
            promociones=[Promocion(4, "15% de descuento de lunes a miércoles", *vigente, "No acumulable")],
        ),
        Restaurante(
            id=7,
            nombre="Verde Raíz",
            descripcion="Cocina vegetariana y vegana con ingredientes de temporada.",
            categoria="Vegetariana",
            ubicacion=Ubicacion("Av. Jardín 77", 29.0880, -110.9990, "Zona Poniente"),
            horario=h(frozenset({0, 1, 2, 3, 4, 5}), "09:00", "18:00"),
            formas_pago=frozenset({DEBITO, CREDITO}),
            precio_promedio=180,
            fecha_apertura=date(2022, 8, 1),
            locatario_id=6,
            menus=_menu(
                ("Bowl de quinoa", 160, "Garbanzo, aguacate y aderezo de tahini"),
                ("Tacos de coliflor", 140, "Al pastor vegetal"),
                ("Jugo verde", 65, "Nopal, piña y apio"),
            ),
        ),
        Restaurante(
            id=8,
            nombre="Antojitos Doña Chayo",
            descripcion="Cocina casera: gorditas, enchiladas y caldo de queso.",
            categoria="Comida mexicana",
            ubicacion=Ubicacion("Calle Morelos 210", 29.0700, -110.9600, "Centro"),
            horario=h(frozenset({0, 1, 2, 3, 4, 5}), "08:00", "16:00"),
            formas_pago=frozenset({EFECTIVO}),
            precio_promedio=90,
            fecha_apertura=date(2005, 1, 20),
            locatario_id=6,
            menus=_menu(
                ("Gorditas de picadillo (3)", 85, "Con salsa de la casa"),
                ("Enchiladas sonorenses", 110, "Con papa y lechuga"),
                ("Caldo de queso", 95, "Receta tradicional"),
            ),
        ),
    ]


# (usuario, restaurante, importe, días atrás, estado final, calificación, comentario)
_TRANSACCIONES: list[tuple[int, int, int, int, EstadoTransaccion, int | None, str | None]] = [
    (1, 1, 540, 20, EstadoTransaccion.COMPLETADA, 5, "El aguachile estaba fresquísimo y la atención fue rápida."),
    (1, 2, 210, 6, EstadoTransaccion.COMPLETADA, None, None),  # lista para evaluar en la demo
    (1, 6, 380, 15, EstadoTransaccion.COMPLETADA, 3, "Buena pizza, pero tardaron casi una hora en servir."),
    (1, 8, 190, 12, EstadoTransaccion.COMPLETADA, 5, "Sabor casero de verdad; las enchiladas son las mejores."),
    (1, 3, 165, 2, EstadoTransaccion.CONFIRMADA, None, None),
    (1, 4, 700, 1, EstadoTransaccion.PENDIENTE, None, None),
    (1, 5, 420, 9, EstadoTransaccion.CANCELADA, None, None),
    (2, 1, 460, 25, EstadoTransaccion.COMPLETADA, 4, "Muy buen coctel, el lugar se llena a mediodía."),
    (2, 4, 890, 18, EstadoTransaccion.COMPLETADA, 5, "La arrachera en su punto y excelente servicio."),
    (2, 5, 510, 10, EstadoTransaccion.COMPLETADA, 3, "El ramen bien, aunque los rollos llegaron tibios."),
    (2, 3, 140, 4, EstadoTransaccion.COMPLETADA, None, None),
    (3, 2, 175, 14, EstadoTransaccion.COMPLETADA, 5, "Los tacos de tripitas valen cada peso. Volveré."),
    (3, 6, 420, 11, EstadoTransaccion.COMPLETADA, 4, "Masa delgada y crujiente; buen ambiente familiar."),
    (3, 7, 310, 8, EstadoTransaccion.COMPLETADA, 5, "Opciones veganas creativas y porciones generosas."),
    (3, 8, 160, 7, EstadoTransaccion.COMPLETADA, 4, "Rico y económico, solo aceptan efectivo."),
    (3, 1, 300, 1, EstadoTransaccion.PENDIENTE, None, None),
]


def cargar_datos_demo(
    usuarios: IRepositorioUsuarios,
    restaurantes: IRepositorioRestaurantes,
    transacciones: IRepositorioTransacciones,
    evaluaciones: IRepositorioEvaluaciones,
    ahora: datetime,
) -> None:
    for usuario in _usuarios():
        usuarios.guardar(usuario)
    for restaurante in _restaurantes(ahora.date()):
        restaurantes.guardar(restaurante)

    for usuario_id, restaurante_id, importe, dias, estado, calificacion, comentario in _TRANSACCIONES:
        locatario = restaurantes.obtener(restaurante_id).locatario_id
        inicio = (ahora - timedelta(days=dias)).replace(hour=14, minute=0, second=0, microsecond=0)
        t = Transaccion(transacciones.siguiente_id(), usuario_id, restaurante_id, importe, inicio, usuario_id)
        t.enviar(inicio, usuario_id)
        if estado is EstadoTransaccion.CANCELADA:
            t.cancelar(inicio + timedelta(minutes=5), usuario_id, "Cancelada por el cliente")
        if estado in (EstadoTransaccion.CONFIRMADA, EstadoTransaccion.COMPLETADA):
            t.confirmar(inicio + timedelta(minutes=10), locatario)
        if estado is EstadoTransaccion.COMPLETADA:
            t.completar(inicio + timedelta(hours=1), locatario)
        transacciones.guardar(t)

        if calificacion is not None:
            evaluacion = Evaluacion.crear(
                id=evaluaciones.siguiente_id(),
                transaccion=t,
                calificacion=calificacion,
                comentario=comentario,
                fecha=inicio + timedelta(hours=3),
            )
            evaluaciones.guardar(evaluacion)
            t.vincular_evaluacion(evaluacion.id)
