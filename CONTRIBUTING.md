# Guía para contribuir

## Preparar el entorno

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest && ruff check .
```

## Reglas del proyecto

1. **Las reglas de negocio viven en `dominio/`.** Ni la interfaz ni los servicios deciden si una transacción puede evaluarse.
2. **El dominio no importa** Gradio, pandas ni nada de `infraestructura/` o `presentacion/`.
3. **Toda regla nueva lleva un ID** (`RN-xx`) en `docs/03_requisitos_y_reglas.md` y al menos una prueba que lo mencione.
4. **El estado de una transacción solo cambia con sus métodos** (`enviar`, `confirmar`, `completar`, `cancelar`).
5. **Nombres en español**, siguiendo PEP 8 (`snake_case` para funciones, `PascalCase` para clases).
6. **Sin datos personales reales** en el repositorio, ni siquiera en pruebas.

## Ramas y commits

- Ramas: `feature/…`, `fix/…`, `docs/…`.
- Commits en español, en imperativo: «Agrega filtro por zona», «Corrige cálculo de distancia».
- Todo cambio entra por *Pull Request* con las pruebas en verde.

## Lista de verificación del Pull Request

- [ ] `pytest` pasa y no baja la cobertura.
- [ ] `ruff check .` sin errores.
- [ ] Documentación actualizada (`docs/` y `CHANGELOG.md`).
- [ ] Matriz de trazabilidad actualizada si se agregó una HU o RN.
