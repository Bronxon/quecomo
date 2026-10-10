# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Versionado [SemVer](https://semver.org/lang/es/).

## [0.2.0] — 2026-10-10

### Eliminado
- Opción de pago en línea **«Transferencia»** en toda la interfaz: filtro de búsqueda, ficha del restaurante, comparación, formulario del locatario y datos de demostración.

### Agregado
- **RN-07:** ¿Qué Como? no ofrece ni procesa pagos en línea. Solo se aceptan formas de pago en el local (efectivo, tarjeta de débito, tarjeta de crédito), validadas en el dominio.
- Aviso en «Mis transacciones» y en «Acerca de»: la app no procesa pagos; se paga en el restaurante.
- 4 pruebas nuevas (114 en total).

### Cambiado
- Etiquetas: «Forma de pago en el local», «Formas de pago aceptadas en el local», «Pago en el local» (comparación), «Importe consumido (MXN)».

## [0.1.1] — 2026-10-10

### Agregado
- Despliegue en Render: `render.yaml` y `.python-version` (Python 3.13).

### Corregido
- `app.py` escucha en `0.0.0.0:$PORT` cuando la plataforma define `PORT`; en local sigue usando `127.0.0.1:7860`.

## [0.1.0] — 2026-10-10

Primera versión del MVP, construida a partir del *Documento Fundamental de Desarrollo* (Actividades 1–4).

### Agregado
- Dominio: `Usuario`, `Restaurante`, `Transaccion` (máquina de estados con historial), `Evaluacion`, `Menu`, `Producto`, `Promocion`, `Ubicacion`, `Horario`.
- Caso de uso CU-01 con `ControladorEvaluacion` y todas sus extensiones.
- Búsqueda con 8 filtros y 4 criterios de orden; comparación de 2 a 3 restaurantes; ficha completa.
- Registro y control de transacciones con autorización por rol (CA-08).
- Panel del locatario (HU-09, HU-10, HU-11) y panel de administración con moderación.
- Interfaz web en Gradio con datos ficticios e inicio de sesión simulado.
- 110 pruebas automatizadas y CI en GitHub Actions.
- Documentación en español: visión, historias, requisitos, CU-01, dominio, arquitectura, diseño dinámico, trazabilidad, pruebas, análisis legal preliminar y validación de negocio.

### Decisiones respecto al documento original
- `buscarPorUsuarioYEstablecimiento` devuelve una lista (puede haber varias transacciones).
- `Evaluacion.registrar()` se asignó al repositorio (`guardar`) para reducir acoplamiento.
- Se agregaron `Horario`, roles de usuario, estado de evaluación y la relación Locatario → Restaurante.
- El administrador no puede confirmar ni completar transacciones.
- El ranking muestra el promedio simple pero ordena con un promedio ponderado.

### Pendiente
- HU-12 / RN-02 (evaluación del restaurante hacia el cliente).
- Persistencia, autenticación real, aviso de privacidad y términos de uso.
- Mitigación del sesgo del locatario.
