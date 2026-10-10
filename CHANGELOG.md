# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Versionado [SemVer](https://semver.org/lang/es/).

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
