"""¿Qué Como? — Plataforma de consulta, comparación y evaluación de restaurantes.

El paquete está organizado en cuatro capas (ver ``docs/06_arquitectura.md``):

- ``dominio``: entidades, estados y reglas de negocio (RN-01 a RN-06).
- ``aplicacion``: controladores y servicios que coordinan los casos de uso.
- ``infraestructura``: repositorios concretos y datos de demostración.
- ``presentacion``: interfaz web construida con Gradio.

La regla central del producto: una evaluación solo es válida si está
respaldada por una transacción COMPLETADA que aún no haya sido evaluada.
"""

__version__ = "0.3.0"
