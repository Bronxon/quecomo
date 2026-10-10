# 07 · Diseño dinámico

> Fuente: Documento Fundamental, sección 10.

## Diagrama de secuencia — CU-01

```mermaid
sequenceDiagram
    autonumber
    actor U as Usuario
    participant V as Vista (Gradio)
    participant C as ControladorEvaluacion
    participant RT as RepositorioTransacciones
    participant T as Transaccion
    participant E as Evaluacion
    participant RE as RepositorioEvaluaciones

    U->>V: Evaluar restaurante (transacción #id)
    V->>C: solicitar_evaluacion(usuario_id, transaccion_id)
    C->>RT: obtener(transaccion_id)
    RT-->>C: transaccion
    C->>T: verificar_evaluable_por(usuario_id)
    alt transacción válida
        T-->>C: ok
        C-->>V: transaccion
        V-->>U: muestra formulario
        U->>V: calificación + comentario
        V->>C: registrar_evaluacion(...)
        Note over C: Repite las validaciones 3–5<br/>bajo un candado (RN-06)
        C->>E: Evaluacion.crear(transaccion, ...)
        E->>E: validar()
        alt datos válidos
            C->>RE: guardar(evaluacion)
            RE-->>C: confirmación
            C->>T: vincular_evaluacion(evaluacion.id)
            C-->>V: evaluacion
            V-->>U: ✅ evaluación registrada
        else datos inválidos
            E-->>C: DatosInvalidos
            V-->>U: ⛔ solicita corrección
        end
    else transacción inválida o inexistente
        T-->>C: EvaluacionNoPermitida(motivo)
        V-->>U: ⛔ informa el motivo
    end
```

## Fragmentos alternativos

| Guarda | Comportamiento |
|---|---|
| `[transacción válida]` | Habilitar evaluación → crear y validar → guardar → vincular → confirmar |
| `[transacción inválida o inexistente]` | Rechazar e informar el motivo (`MotivoRechazo`) |
| `[datos válidos]` | Guardar |
| `[datos inválidos]` | Solicitar corrección; la transacción sigue disponible |

## Máquina de estados de Transacción

```mermaid
stateDiagram-v2
    [*] --> INICIADA: registrar (cliente)
    INICIADA --> PENDIENTE: enviar (automático al registrar)
    PENDIENTE --> CONFIRMADA: confirmar (locatario)
    CONFIRMADA --> COMPLETADA: completar (locatario)
    PENDIENTE --> CANCELADA: cancelar (cliente o locatario)
    CONFIRMADA --> CANCELADA: cancelar (cliente o locatario)
    COMPLETADA --> [*]
    CANCELADA --> [*]

    note right of COMPLETADA
        [estado == COMPLETADA AND noExisteEvaluacion]
        → puede_evaluarse() = true
    end note
```

| Estado | Significado |
|---|---|
| INICIADA | La operación acaba de comenzar |
| PENDIENTE | En espera de confirmación del restaurante |
| CONFIRMADA | El restaurante la confirmó |
| COMPLETADA | La relación comercial concluyó; **puede** respaldar una evaluación |
| CANCELADA | Terminó sin completarse; **nunca** respalda una evaluación |

Las transiciones permitidas están en `TRANSICIONES_TRANSACCION` (`dominio/estados.py`). Cualquier otra —por ejemplo **CANCELADA → COMPLETADA**— lanza `TransicionInvalida`. Cada transición queda en `Transaccion.historial` con fecha, actor y nota.

## Estados de Evaluación (agregado)

```mermaid
stateDiagram-v2
    direction LR
    [*] --> PUBLICADA: registrar
    PUBLICADA --> OCULTA: ocultar(motivo) · administrador
    OCULTA --> PUBLICADA: restaurar · administrador
```

Una evaluación **OCULTA** no cuenta para el ranking, pero la transacción **no se libera**: no puede respaldar una nueva evaluación.
