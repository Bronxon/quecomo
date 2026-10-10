"""Punto de entrada de ¿Qué Como?

Uso:
    python app.py

Variables de entorno opcionales:
    QUECOMO_ZONA_HORARIA   Zona horaria para «abierto ahora» (por defecto America/Hermosillo).
    GRADIO_SERVER_NAME     Dirección de escucha (usa 0.0.0.0 para exponerla en la red).
    GRADIO_SERVER_PORT     Puerto (por defecto 7860).
"""

import sys
from pathlib import Path

# Permite ejecutar `python app.py` sin instalar el paquete.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from quecomo.presentacion.interfaz import CSS, TEMA, construir_interfaz  # noqa: E402

demo = construir_interfaz()

if __name__ == "__main__":
    demo.launch(theme=TEMA, css=CSS)
