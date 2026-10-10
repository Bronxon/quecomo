"""Punto de entrada de ¿Qué Como?

Uso local:
    python app.py                      → http://127.0.0.1:7860

En la nube (Render, Railway, etc.) la plataforma define la variable PORT;
en ese caso la app escucha en 0.0.0.0:$PORT automáticamente.

Variables de entorno opcionales:
    PORT                   Puerto asignado por la plataforma de despliegue.
    QUECOMO_ZONA_HORARIA   Zona horaria para «abierto ahora» (por defecto America/Hermosillo).
    GRADIO_SERVER_NAME     Dirección de escucha (sobrescribe el valor automático).
    GRADIO_SERVER_PORT     Puerto (sobrescribe el valor automático).
"""

import os
import sys
from pathlib import Path

# Permite ejecutar `python app.py` sin instalar el paquete.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from quecomo.presentacion.interfaz import CSS, TEMA, construir_interfaz  # noqa: E402

demo = construir_interfaz()


def configuracion_servidor() -> tuple[str, int]:
    """Host y puerto: en la nube usa 0.0.0.0:$PORT; en local, 127.0.0.1:7860."""
    puerto_nube = os.getenv("PORT")
    host = os.getenv("GRADIO_SERVER_NAME") or ("0.0.0.0" if puerto_nube else "127.0.0.1")
    puerto = int(os.getenv("GRADIO_SERVER_PORT") or puerto_nube or 7860)
    return host, puerto


if __name__ == "__main__":
    host, puerto = configuracion_servidor()
    demo.launch(server_name=host, server_port=puerto, theme=TEMA, css=CSS)
