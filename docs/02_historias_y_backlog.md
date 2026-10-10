# 02 · Historias de usuario y backlog

> Fuente: Documento Fundamental, sección 3. La columna **Estado en el MVP** se agregó para este repositorio.

## Historias de usuario

| ID | Historia | Prioridad | Estado en el MVP | Dónde |
|---|---|---|---|---|
| HU-01 | Como usuario, quiero **buscar** restaurantes para encontrar alternativas disponibles. | Alta | ✅ Implementada | `ServicioBusqueda.buscar` · pestaña Buscar |
| HU-02 | Como usuario, quiero **filtrar** por precio, distancia, horario y forma de pago para reducir las opciones. | Alta | ✅ Implementada (además: tipo de comida, calificación mínima, promociones) | `CriteriosBusqueda` |
| HU-03 | Como usuario, quiero **consultar la información** de un restaurante antes de elegir. | Alta | ✅ Implementada | `ServicioBusqueda.detalle` · pestaña Ficha |
| HU-04 | Como usuario, quiero **comparar** restaurantes para apoyar mi decisión. | Media | ✅ Implementada (2 a 3 restaurantes) | `ServicioBusqueda.comparar` · pestaña Comparar |
| HU-05 | Como usuario, quiero consultar **ranking y evaluaciones**. | Media | ✅ Implementada | `ServicioRanking` |
| HU-06 | Como usuario, quiero **registrar una transacción** para dejar evidencia de la relación comercial. | Alta | ✅ Implementada | `ServicioTransacciones.registrar` · Evaluar › «Registrar un consumo nuevo» (en la interfaz se llama *consumo*) |
| HU-07 | Como usuario, quiero **evaluar** un restaurante después de una transacción válida. | Alta | ✅ Implementada | `ControladorEvaluacion.registrar_evaluacion` · pestaña Evaluar |
| HU-08 | Como sistema, quiero **validar que exista una transacción** antes de permitir una evaluación. | Alta | ✅ Implementada | `Transaccion.puede_evaluarse` |
| HU-09 | Como locatario, quiero **registrar mi restaurante**. | Media | ✅ Implementada | `ServicioRestaurantes.registrar` |
| HU-10 | Como locatario, quiero **administrar la información** de mi restaurante. | Media | ✅ Implementada (datos, menú, promociones) | `ServicioRestaurantes.actualizar` |
| HU-11 | Como locatario, quiero **consultar las evaluaciones recibidas**. | Baja | ✅ Implementada | `ServicioRestaurantes.evaluaciones_recibidas` |
| HU-12 | Como usuario/restaurante, quiero **evaluar a la contraparte** cuando la regla lo permita. | Baja | ⏳ Pendiente (RN-02 depende de una decisión de negocio) | — |

## Backlog priorizado

| Prioridad | Historias | Enfoque |
|---|---|---|
| Alta | HU-01, HU-02, HU-03, HU-06, HU-07, HU-08 | Búsqueda, filtros, información, transacción y mecanismo de confianza |
| Media | HU-04, HU-05, HU-09, HU-10 | Comparación, ranking y administración de restaurantes |
| Baja / posterior | HU-11, HU-12 | Retroalimentación adicional y funciones futuras |

La selección para profundizar el diseño fue **HU-08** junto con **HU-07**: validar que exista una transacción válida antes de habilitar la evaluación (ver [04 · CU-01](04_caso_de_uso_CU01.md)).

## Historias técnicas agregadas durante la implementación

| ID | Historia | Motivo |
|---|---|---|
| HT-01 | Como administrador, quiero **ocultar evaluaciones con un motivo** y poder restaurarlas. | Moderación (rol Administrador, sección 2.1) y transparencia |
| HT-02 | Como sistema, quiero que **solo el locatario dueño** confirme y complete transacciones. | Requisito de Seguridad y CA-08 |
| HT-03 | Como sistema, quiero **impedir evaluaciones duplicadas** aun con solicitudes simultáneas. | Fiabilidad y RN-06 |
| HT-04 | Como usuario, quiero que el orden por ranking **no favorezca** a restaurantes con muy pocas evaluaciones. | Calidad de la información para decidir |

## Criterios de aceptación por historia (propuesta)

Formato *Dado / Cuando / Entonces* para las historias de prioridad alta:

**HU-06 — Registrar transacción**
- *Dado* un cliente activo y un restaurante activo, *cuando* registra un importe mayor que cero, *entonces* se crea una transacción **PENDIENTE** vinculada a ambos.
- *Dado* un restaurante suspendido, *cuando* el cliente intenta registrar, *entonces* el sistema lo rechaza.

**HU-07 / HU-08 — Evaluar después de una transacción**
- *Dado* una transacción **COMPLETADA** sin evaluación, *cuando* su dueño califica (1–5) y comenta (≥ 10 caracteres), *entonces* la evaluación se registra y queda vinculada.
- *Dado* una transacción **PENDIENTE, CONFIRMADA o CANCELADA**, *cuando* se solicita evaluar, *entonces* se rechaza indicando el motivo.
- *Dado* una transacción **ya evaluada**, *cuando* se intenta evaluar de nuevo, *entonces* se rechaza.
- *Dado* una transacción de **otro usuario**, *cuando* se intenta usarla, *entonces* se rechaza.
