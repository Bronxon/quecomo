# 03 · Requisitos, calidad y reglas de negocio

> Fuente: Documento Fundamental, sección 4. Se agrega la columna **Implementación** para mantener la trazabilidad con el código.

## Reglas de negocio

| ID | Regla | Implementación |
|---|---|---|
| RN-01 | Un usuario puede evaluar un restaurante únicamente cuando existe una transacción válida entre ambos. | `Transaccion.verificar_evaluable_por()` (dueño + estado) · `ControladorEvaluacion.solicitar_evaluacion()` |
| RN-02 | Un restaurante puede evaluar a un usuario solo con transacción válida, **si la función se habilita**. | ⏳ Pendiente (HU-12) |
| RN-03 | Toda evaluación debe poder rastrearse hasta la transacción que la respalda. | `Evaluacion.transaccion_id` + `Transaccion.evaluacion_id`; la ficha muestra «Respaldada por la transacción #N» |
| RN-04 | Una evaluación no puede usarse para crear posteriormente una transacción. | `Evaluacion.crear()` exige una transacción ya evaluable; no existe operación inversa |
| RN-05 | Una transacción cancelada o incompleta no habilita la evaluación. | `Transaccion.es_valida()` → solo `COMPLETADA` |
| RN-06 | Una transacción ya utilizada no habilita otra evaluación. | `Transaccion.vincular_evaluacion()` + candado del controlador + unicidad en `RepositorioEvaluaciones.guardar()` |
| RN-07 | ¿Qué Como? no ofrece ni procesa pagos en línea. Solo se informan formas de pago en el local: efectivo, tarjeta de débito y tarjeta de crédito. *(Agregada en v0.2.0.)* | `FORMAS_PAGO_PERMITIDAS` y validación en `Restaurante.__post_init__()` |

## Requisitos funcionales

| ID | Requisito | Implementación |
|---|---|---|
| RF-01 | Buscar restaurantes | `ServicioBusqueda.buscar` |
| RF-02 | Filtrar por criterios relevantes | `CriteriosBusqueda` (8 filtros) |
| RF-03 | Mostrar información del restaurante | `ServicioBusqueda.detalle` · `Vista.ficha` |
| RF-04 | Comparar alternativas | `ServicioBusqueda.comparar` |
| RF-05 | Registrar transacciones | `ServicioTransacciones.registrar` |
| RF-06 | Consultar transacciones para validar la posibilidad de evaluar | `ControladorEvaluacion.transacciones_evaluables` |
| RF-07 | Registrar una evaluación cuando se cumplan las reglas | `ControladorEvaluacion.registrar_evaluacion` |
| RF-08 | Rechazar evaluaciones sin transacción válida | `EvaluacionNoPermitida` con `MotivoRechazo` |
| RF-09 | Asociar la evaluación con usuario, restaurante y transacción | `Evaluacion.crear` toma los tres datos **de la transacción**, no de la interfaz |
| RF-10 | Actualizar el ranking a partir de evaluaciones válidas | `ServicioRanking.calcular` (solo evaluaciones PUBLICADAS) |

## Requisitos de calidad

| Atributo | Aplicación | Cómo se cumple |
|---|---|---|
| Integridad | Las evaluaciones mantienen su relación con transacciones válidas | Vínculo bidireccional y restricción de unicidad |
| Seguridad | Estados y reglas no se modifican arbitrariamente desde la interfaz | `estado` es propiedad de solo lectura; transiciones solo por métodos; autorización por rol en `aplicacion/autorizacion.py` |
| Trazabilidad | Saber qué usuario, restaurante y transacción respaldan una evaluación | `historial` de cada transacción con fecha y actor |
| Fiabilidad | Rechazar estados y operaciones inconsistentes | `TransicionInvalida`; prueba de concurrencia con 8 hilos |
| Cohesión | Cada clase con responsabilidades relacionadas | Un servicio por grupo de casos de uso |
| Bajo acoplamiento | El dominio no depende de la interfaz ni de detalles técnicos | El paquete `dominio` no importa Gradio ni la infraestructura |

## Requisitos no funcionales agregados para el MVP

| ID | Requisito | Estado |
|---|---|---|
| RNF-01 | La interfaz debe estar completamente en español. | ✅ |
| RNF-02 | Los mensajes de rechazo deben explicar el motivo con lenguaje claro. | ✅ |
| RNF-03 | Las reglas de negocio deben tener pruebas automatizadas. | ✅ 114 pruebas, CI en GitHub Actions |
| RNF-04 | Publicar solo el nombre y la inicial del apellido de quien evalúa (minimización de datos). | ✅ `Usuario.nombre_publico()` |
| RNF-05 | No mostrar públicamente el importe de las transacciones. | ✅ |
| RNF-06 | Comentarios de 10 a 500 caracteres; calificación entera de 1 a 5. | ✅ `Evaluacion.validar()` |

## Decisiones que el documento original dejaba abiertas

| Tema | Decisión en el MVP | Por qué |
|---|---|---|
| ¿Quién mueve el estado de la transacción? | Cliente registra/cancela; **solo el locatario dueño** confirma y completa. | Evita que el cliente se habilite a sí mismo (CA-08). |
| ¿Puede el administrador completar transacciones? | **No.** Puede suspender restaurantes y moderar evaluaciones. | Nadie ajeno a la relación comercial debe fabricar evidencia. |
| ¿Ocultar una evaluación libera la transacción? | **No.** | Evita borrar y reescribir evaluaciones para manipular el ranking. |
| ¿Hay plazo para evaluar? | No en el MVP. | Pendiente de decisión de negocio. |
| ¿Se ofrecen pagos en línea? | **No** (RN-07). Se eliminó «Transferencia» y la interfaz aclara que se paga en el local. | Observación de revisión del proyecto (v0.2.0): mantener el alcance en consulta y evaluación, sin manejo de dinero. |
