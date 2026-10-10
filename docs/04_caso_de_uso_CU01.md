# 04 · Caso de uso CU-01 — Evaluar restaurante después de una transacción

> Fuente: Documento Fundamental, sección 5. Realización: `src/quecomo/aplicacion/controlador_evaluacion.py`.

| Elemento | Definición |
|---|---|
| **Actor principal** | Usuario (Cliente) |
| **Objetivo** | Registrar una evaluación únicamente cuando existe una relación comercial válida |
| **Disparador** | El usuario pulsa «Evaluar restaurante» |
| **Precondiciones** | Usuario registrado y activo; restaurante registrado y activo; existe una transacción del usuario con el restaurante; la transacción cumple las condiciones |
| **Garantía de éxito** | La evaluación queda registrada y vinculada a usuario, restaurante y transacción |

## Flujo principal y su realización

| Paso | Interacción | Código |
|---|---|---|
| 1 | El usuario selecciona la transacción («consumo» en la interfaz) a evaluar | Pestaña Evaluar · `Vista.opciones_para_evaluar` |
| 2 | El sistema identifica al usuario y consulta sus transacciones | `ControladorEvaluacion._usuario_habilitado` · `IRepositorioTransacciones` |
| 3 | El sistema obtiene la transacción correspondiente | `ControladorEvaluacion._obtener_transaccion` |
| 4 | El sistema solicita a la transacción determinar si puede evaluarse | `transaccion.verificar_evaluable_por(usuario.id)` |
| 5 | La transacción valida su estado y condiciones | `Transaccion.puede_evaluarse()` — *Information Expert* |
| 6 | Si es válida, se habilita el formulario | `Vista.solicitar_evaluacion` → formulario visible |
| 7 | El usuario proporciona calificación y comentario | Radio 1–5 y cuadro de texto |
| 8 | El sistema valida la evaluación | `Evaluacion.crear(...)` → `validar()` |
| 9 | El sistema registra la evaluación | `RepositorioEvaluaciones.guardar(evaluacion)` |
| 10 | El sistema la relaciona con usuario, restaurante y transacción | `transaccion.vincular_evaluacion(evaluacion.id)` |
| 11 | El sistema actualiza la información del ranking | `ServicioRanking.calcular` (se recalcula al consultar) |
| 12 | El sistema confirma el registro | Mensaje «✅ Evaluación publicada… vinculada a tu consumo #N» |

> **Importante:** en el paso 9 se **repiten** todas las validaciones de los pasos 2 a 5. La interfaz nunca se considera fuente confiable.

## Extensiones

| Condición | Respuesta del sistema | Motivo (`MotivoRechazo`) | Prueba |
|---|---|---|---|
| No existe transacción | Rechaza e informa que se requiere una transacción válida | `SIN_TRANSACCION` | `test_ca07_sin_transaccion_es_rechazada` |
| Transacción PENDIENTE o CONFIRMADA | No habilita el formulario | `TRANSACCION_NO_COMPLETADA` | `test_ca04_transaccion_incompleta_no_habilita` |
| Transacción CANCELADA | No habilita el formulario | `TRANSACCION_CANCELADA` | `test_ca04_rn05_transaccion_cancelada_no_habilita` |
| Transacción ya utilizada | Rechaza una segunda evaluación | `TRANSACCION_YA_EVALUADA` | `test_rn06_una_sola_evaluacion_por_transaccion` |
| Transacción de otro usuario | Rechaza | `TRANSACCION_AJENA` | `test_rn01_no_se_puede_usar_la_transaccion_de_otro` |
| Evaluación incompleta | Solicita los datos obligatorios; no registra nada | `DatosInvalidos` | `test_extension_evaluacion_incompleta` |
| Restaurante no disponible | No permite el registro | `RESTAURANTE_NO_DISPONIBLE` | `test_extension_restaurante_no_disponible` |
| Usuario bloqueado | No permite el registro | `USUARIO_NO_HABILITADO` | `test_usuario_bloqueado_no_puede_evaluar` |
| Cancelación por el usuario | No se crea ningún registro | — | El formulario se oculta al cambiar de transacción |
| Dos solicitudes simultáneas | Solo una se registra | `TRANSACCION_YA_EVALUADA` | `test_concurrencia_no_duplica_evaluaciones` |
