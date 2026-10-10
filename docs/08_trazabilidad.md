# 08 · Trazabilidad

> Fuente: Documento Fundamental, sección 11, extendida hasta el código y las pruebas.

## Cadena de ingeniería

| Actividad | Secuencia | Documento en este repositorio |
|---|---|---|
| 1 | Problema → Usuarios → Visión → Escenario → Historias → Backlog | [01](01_vision_y_usuarios.md), [02](02_historias_y_backlog.md) |
| 2 | Historia prioritaria → Necesidades → Caso de uso → Modelo de dominio | [03](03_requisitos_y_reglas.md), [04](04_caso_de_uso_CU01.md), [05](05_modelo_de_dominio.md) |
| 3 | Modelo de dominio → Responsabilidades → GRASP → Clases → Arquitectura | [06](06_arquitectura.md) |
| 4 | Clases + Caso de uso → Secuencia → Estados → Guardas | [07](07_diseno_dinamico.md) |
| **5 (este repositorio)** | **Implementación → Pruebas → MVP** | `src/`, `tests/`, [09](09_pruebas.md) |

## Matriz de trazabilidad extendida

| Origen | Artefacto | Código | Pruebas |
|---|---|---|---|
| Necesidad de decidir mejor | HU-01, HU-02 | `ServicioBusqueda.buscar`, `CriteriosBusqueda` | `test_busqueda.py::TestCA02Filtros` |
| Necesidad de decidir mejor | HU-03, HU-05 | `ServicioBusqueda.detalle`, `ServicioRanking` | `test_vista.py::test_ficha_muestra_evaluaciones_con_trazabilidad`, `test_busqueda.py::TestRanking` |
| Necesidad de decidir mejor | HU-04 | `ServicioBusqueda.comparar` | `test_busqueda.py::TestComparar` |
| Problema de confianza | HU-06 | `ServicioTransacciones.registrar` | `test_ca03_registrar_transaccion` |
| Problema de confianza | HU-07, HU-08 → CU-01 | `ControladorEvaluacion` | `test_controlador_evaluacion.py` |
| CU-01 | Modelo de dominio | `Usuario`, `Restaurante`, `Transaccion`, `Evaluacion` | `test_transaccion.py` |
| Transacción | Information Expert | `Transaccion.puede_evaluarse()` | `TestPuedeEvaluarse` |
| CU-01 | Controller | `ControladorEvaluacion` | `test_ca05_ca06_flujo_principal` |
| CU-01 | Diagrama de secuencia | `solicitar_evaluacion` / `registrar_evaluacion` | `test_flujo_cu01_desde_la_vista` |
| Transacción | Máquina de estados | `TRANSICIONES_TRANSACCION` | `TestCicloDeVida` |
| Regla de evaluación | Guarda `[COMPLETADA AND noExisteEvaluacion]` | `puede_evaluarse()` | `test_completada_sin_evaluacion_habilita`, `test_ya_evaluada_no_habilita_otra` |
| Seguridad | CA-08 | `autorizacion.exigir_propietario(..., permitir_admin=False)` | `TestCA08ControlDeEstados` |
| Fiabilidad | RN-06 | Candado + unicidad en repositorio | `test_concurrencia_no_duplica_evaluaciones`, `test_repositorio_rechaza_duplicado_como_restriccion_unica` |
| Revisión del proyecto | RN-07 sin pagos en línea | `FORMAS_PAGO_PERMITIDAS`, validación de `Restaurante` | `test_rn07_no_hay_pagos_en_linea`, `test_rn07_interfaz_sin_pagos_en_linea` |
| Rol Administrador | Moderación (HT-01) | `ServicioRestaurantes.ocultar_evaluacion` | `TestAdministrador` |
| Locatario | HU-09, HU-10, HU-11 | `ServicioRestaurantes` | `test_restaurantes.py` |

## Cómo mantener la matriz

1. Toda historia nueva recibe un ID (`HU-xx`) y se agrega a [02](02_historias_y_backlog.md).
2. Toda regla nueva recibe un ID (`RN-xx`) en [03](03_requisitos_y_reglas.md).
3. Las pruebas que la verifican mencionan el ID en su nombre o docstring.
4. Los cambios de diseño se registran en [`CHANGELOG.md`](../CHANGELOG.md) y en la tabla ADR de [06](06_arquitectura.md).
