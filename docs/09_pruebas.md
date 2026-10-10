# 09 · Estrategia de pruebas

## Cómo ejecutar

```bash
pip install -r requirements-dev.txt
pytest                                                   # todas
pytest tests/test_controlador_evaluacion.py -v           # solo CU-01
pytest -k "ca08 or CA08"                                 # por criterio
pytest --cov=quecomo --cov-report=html                   # informe en htmlcov/index.html
```

Las pruebas también se ejecutan automáticamente en GitHub Actions en cada *push* y *pull request* (Python 3.10, 3.12 y 3.13) — ver `.github/workflows/pruebas.yml`.

## Niveles

| Nivel | Archivo | Qué verifica |
|---|---|---|
| Unitarias (dominio) | `test_transaccion.py` | Máquina de estados, importe, guarda `puede_evaluarse` |
| Integración (CU-01) | `test_controlador_evaluacion.py` | Flujo principal, todas las extensiones, concurrencia |
| Integración (servicios) | `test_servicio_transacciones.py`, `test_busqueda.py`, `test_restaurantes.py` | Autorización, filtros, orden, comparación, administración |
| Presentación | `test_vista.py` | Que la interfaz se construye y que la vista traduce bien los errores |

Todas usan un **reloj fijo** (sábado 10/10/2026, 13:00) definido en `tests/conftest.py`, por lo que son deterministas.

## Criterios de aceptación → pruebas

| ID | Criterio | Prueba(s) |
|---|---|---|
| CA-01 | Un usuario puede consultar restaurantes disponibles | `test_ca01_consultar_restaurantes_disponibles` |
| CA-02 | El usuario puede aplicar criterios de búsqueda y filtrado | `TestCA02Filtros` (9 pruebas) |
| CA-03 | Se registra una transacción relacionada con usuario y restaurante | `test_ca03_registrar_transaccion` |
| CA-04 | Una transacción incompleta o cancelada no habilita una evaluación | `test_ca04_transaccion_incompleta_no_habilita`, `test_ca04_rn05_transaccion_cancelada_no_habilita` |
| CA-05 | Una transacción completada habilita la evaluación si no existe una previa | `test_ca05_ca06_flujo_principal`, `test_completada_sin_evaluacion_habilita` |
| CA-06 | La evaluación queda relacionada con usuario, restaurante y transacción | `test_ca05_ca06_flujo_principal` |
| CA-07 | Una solicitud sin transacción válida es rechazada | `test_ca07_sin_transaccion_es_rechazada` |
| CA-08 | El estado cambia solo mediante operaciones controladas | `test_el_estado_no_se_asigna_directamente`, `TestCA08ControlDeEstados` |

## Reglas de negocio → pruebas

| Regla | Prueba(s) |
|---|---|
| RN-01 | `test_rn01_no_se_puede_usar_la_transaccion_de_otro`, `test_solo_el_dueno_puede_evaluar` |
| RN-03 | `test_ca05_ca06_flujo_principal`, `test_ficha_muestra_evaluaciones_con_trazabilidad` |
| RN-04 | `test_rn04_evaluacion_no_puede_crearse_sin_transaccion_valida` |
| RN-05 | `test_cancelada_no_habilita`, `test_ca04_rn05_transaccion_cancelada_no_habilita` |
| RN-06 | `test_rn06_una_sola_evaluacion_por_transaccion`, `test_concurrencia_no_duplica_evaluaciones`, `test_repositorio_rechaza_duplicado_como_restriccion_unica` |
| RN-07 | `test_rn07_no_hay_pagos_en_linea`, `test_rn07_interfaz_sin_pagos_en_linea`, `test_validaciones_de_registro` |

## Pruebas manuales sugeridas (exploratorias)

| # | Pasos | Resultado esperado |
|---|---|---|
| M-01 | Ana → ⭐ Evaluar → transacción PENDIENTE → «Evaluar restaurante» | ⛔ Mensaje indicando que debe estar COMPLETADA |
| M-02 | Ana → 🏪 Locatario → «Completar» cualquier transacción | ⛔ «Solo el locatario de … puede…» |
| M-03 | Gabriela (admin) → oculta una evaluación sin motivo | ⛔ «El campo motivo de moderación es obligatorio» |
| M-04 | Héctor → registra restaurante con horario «8am» | ⛔ Formato HH:MM |
| M-05 | Buscar con horario «20:00» (de martes a domingo) | Aparece *Tacos La Lumbre* (18:00–02:00) y no *Antojitos Doña Chayo* (08:00–16:00) |
| M-06 | Admin suspende un restaurante | Desaparece de búsqueda, ficha, comparar y registro de transacciones |
