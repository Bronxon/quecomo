# 10 · Cumplimiento legal y protección de datos (análisis preliminar)

> ⚠️ **Aviso.** Este documento es un **análisis preliminar** elaborado para un proyecto académico. **No es asesoría jurídica** ni sustituye la revisión de un abogado. Antes de operar con usuarios reales, los puntos marcados como *Requiere validación* deben revisarse con un profesional y contra las fuentes oficiales vigentes.
>
> Jurisdicción considerada: **México**. Fecha de consulta de fuentes: **10 de octubre de 2026**.

## 1. Ficha jurídico-técnica

| Elemento | Situación actual (MVP) | Situación prevista (producto) |
|---|---|---|
| Producto | Prototipo académico, sin usuarios reales | Plataforma pública de consulta y evaluación de restaurantes |
| Responsables | Equipo del proyecto (ver README) | Persona física o moral a definir |
| Usuarios | Usuarios de demostración ficticios | Público en general y restaurantes |
| Operación | Local / demostración | México |
| Datos personales | Ficticios, en memoria | Nombre, correo, transacciones, evaluaciones y, posiblemente, ubicación |
| Pagos | No hay | No previsto (la transacción es un registro, no un cobro) |
| Contenido de terceros | Textos ficticios | Menús, fotos y logotipos de restaurantes; reseñas de usuarios |
| Uso de IA en el producto | No | No previsto |

## 2. Matriz de aplicabilidad normativa (preliminar)

| Norma | Por qué podría aplicar | Supuesto que la activa | Estado |
|---|---|---|---|
| **Ley Federal de Protección de Datos Personales en Posesión de los Particulares** (nueva ley publicada en el DOF el 20/03/2025, vigente desde el 21/03/2025) | La plataforma trataría datos personales de usuarios y locatarios | Operar con datos de personas reales | Requiere validación |
| **Ley Federal de Protección al Consumidor** | Información y publicidad de restaurantes y promociones; posible rol de intermediario en medios electrónicos | Publicar información comercial u ofertas al público | Requiere validación del rol de la plataforma |
| **Ley Federal del Derecho de Autor** | Protección del código fuente; uso de fotos, menús y textos de terceros | Publicar el código y contenidos | Aplica al código; revisar contenidos |
| **Ley Federal de Protección a la Propiedad Industrial** | Uso de la marca «¿Qué Como?» y de marcas de restaurantes | Uso comercial del nombre | Pendiente búsqueda de anterioridades ante el IMPI |
| Legislación civil y mercantil (contratación electrónica) | Términos y condiciones con usuarios y restaurantes | Aceptación de términos en línea | Requiere validación |

Notas verificadas sobre datos personales: según análisis publicados tras la reforma, la nueva ley es en lo sustancial similar a la anterior, pero exige recabar de nuevo el consentimiento si los datos se usarán para finalidades distintas a las informadas, endurece condiciones del derecho de oposición y amplía el deber de confidencialidad. Las funciones que tenía el INAI en esta materia se transfirieron a la **Secretaría Anticorrupción y Buen Gobierno**. *(Fuentes al final.)*

> No se presentan normas extranjeras (por ejemplo, GDPR) como aplicables. Solo lo serían si se ofreciera el servicio a personas en otras jurisdicciones.

## 3. Inventario de datos personales

| Dato | Titular | Finalidad | ¿Necesario? | Visibilidad pública | En el MVP |
|---|---|---|---|---|---|
| Nombre completo | Usuario, locatario | Identificación en la cuenta | Sí | Solo nombre + inicial del apellido junto a evaluaciones | Ficticio |
| Correo (contacto) | Usuario, locatario | Acceso y comunicaciones | Sí | No | Ficticio, no se muestra |
| Historial de transacciones | Usuario | Respaldar evaluaciones (regla central) | Sí | Solo el ID de la transacción que respalda una evaluación; **nunca el importe** | Ficticio |
| Importe de la transacción | Usuario | Evidencia de consumo | Discutible — evaluar si basta con fecha y restaurante | No | Ficticio |
| Evaluaciones (calificación, comentario) | Usuario | Información para otros usuarios | Sí | Sí | Ficticio |
| Ubicación del usuario | Usuario | Calcular distancias | Opcional | No | **No se recopila**: se usan puntos de referencia predefinidos |
| Datos del locatario como persona | Locatario | Administración de la cuenta | Sí | No | Ficticio |

**Minimización ya aplicada en el código:** `Usuario.nombre_publico()` publica solo el nombre y la inicial del apellido; el importe no se muestra públicamente; no se usa geolocalización del dispositivo.

## 4. Registro de riesgos (escala interna 1–5 × 1–5)

| ID | Riesgo | P | I | Puntaje | Control actual | Acción propuesta | Residual |
|---|---|---|---|---|---|---|---|
| R-01 | Operar con datos reales sin **aviso de privacidad** | 4 | 4 | 16 Crítico | Solo datos ficticios | Redactar aviso de privacidad y mecanismo de consentimiento antes de abrir a usuarios | Bajo |
| R-02 | Sin **autenticación real**: suplantación de usuarios | 5 | 4 | 20 Crítico | Sesión simulada solo para demo | Autenticación con contraseña segura o proveedor externo; nunca publicar la demo con datos reales | Bajo |
| R-03 | **Evaluaciones manipuladas** (cuentas falsas que generan transacciones) | 3 | 4 | 12 Alto | Solo el locatario completa transacciones | Verificación de cuenta, límites por usuario, detección de patrones | Medio |
| R-04 | **Sesgo del locatario**: no completa transacciones de clientes insatisfechos | 3 | 4 | 12 Alto | Ninguno | Ver [11](11_validacion_y_modelo_de_negocio.md#4-riesgo-crítico-el-locatario-controla-la-evidencia) | Medio |
| R-05 | **Moderación** arbitraria u opaca | 2 | 3 | 6 Moderado | Motivo obligatorio; acción reversible | Política de moderación pública y canal de apelación | Bajo |
| R-06 | Afirmar «evaluación verificada» sin evidencia suficiente | 3 | 3 | 9 Moderado | Se dice «respaldada por la transacción #N», no «compra verificada» | Mantener redacción prudente mientras la transacción sea declarativa | Bajo |
| R-07 | Uso de **fotos, logotipos o menús** sin autorización | 3 | 3 | 9 Moderado | No se usan imágenes de terceros | Términos con restaurantes que otorguen licencia de uso | Bajo |
| R-08 | Conflicto con una **marca registrada** «¿Qué Como?» | 2 | 3 | 6 Moderado | Ninguno | Búsqueda fonética y figurativa en el IMPI antes de uso comercial | Bajo |
| R-09 | **Titularidad** del código entre integrantes del equipo / institución | 2 | 3 | 6 Moderado | Licencia MIT en el repositorio | Acordar por escrito la titularidad y revisar el reglamento de la institución | Bajo |

## 5. Requisitos legales traducidos a requisitos técnicos

| ID | Requisito | Fuente | Componente | Criterio de aceptación | Estado |
|---|---|---|---|---|---|
| RL-01 | Mostrar aviso de privacidad antes de recabar datos | LFPDPPP (validar artículos) | Registro de usuario | El usuario no puede crear cuenta sin acceder al aviso | Pendiente |
| RL-02 | Permitir el ejercicio de derechos ARCO | LFPDPPP | Perfil / soporte | Existe un canal y un procedimiento documentado | Pendiente |
| RL-03 | Publicar solo los datos mínimos del autor de una evaluación | Principio de minimización | `Usuario.nombre_publico()` | La ficha no muestra nombre completo (prueba `test_ficha_muestra_evaluaciones_con_trazabilidad`) | ✅ |
| RL-04 | No exponer importes de transacciones | Minimización / confidencialidad | Ficha, búsqueda | No hay importes en vistas públicas | ✅ |
| RL-05 | Registrar quién cambió el estado de cada transacción | Trazabilidad / evidencia | `Transaccion.historial` | Cada cambio guarda fecha, actor y nota | ✅ |
| RL-06 | Moderación con motivo y reversible | Transparencia | `Evaluacion.ocultar(motivo)` | No se puede ocultar sin motivo | ✅ |
| RL-07 | Términos de uso para usuarios y restaurantes | Contratación electrónica | Registro | Aceptación registrada con fecha y versión | Pendiente |
| RL-08 | Conservación y eliminación de datos | LFPDPPP | Persistencia | Plazos definidos y proceso de borrado | Pendiente |

## 6. Inventario de licencias de dependencias

| Componente | Uso | Licencia | Obligación principal |
|---|---|---|---|
| Gradio | Interfaz web | Apache-2.0 | Conservar avisos de licencia y de cambios |
| pandas | Tablas | BSD-3-Clause | Conservar aviso de copyright |
| tzdata | Zonas horarias | Apache-2.0 | Conservar avisos |
| pytest, pytest-cov | Pruebas (desarrollo) | MIT | Conservar aviso |
| ruff | Estilo (desarrollo) | MIT | Conservar aviso |
| Fuente Nunito (Google Fonts) | Tipografía de la interfaz | SIL Open Font License 1.1 | Uso libre; no vender la fuente por separado |

Todas son compatibles con publicar el proyecto bajo **MIT**. Antes de cada versión, revisa las licencias de dependencias nuevas (por ejemplo, con `pip-licenses`).

## 7. Pendientes antes de un lanzamiento real

1. Definir quién es el **responsable** del tratamiento de datos.
2. Aviso de privacidad y términos de uso **revisados por un abogado**.
3. Autenticación real y almacenamiento seguro de credenciales.
4. Política de moderación y canal de apelación.
5. Búsqueda de marca ante el IMPI.
6. Acuerdo escrito de titularidad del código entre integrantes del equipo.
7. Definir si la plataforma actúa como **intermediario** frente a la Ley Federal de Protección al Consumidor.

## Fuentes consultadas (10/10/2026)

- Cámara de Diputados — texto vigente de la LFPDPPP: <https://www.diputados.gob.mx/LeyesBiblio/pdf/LFPDPPP.pdf>
- Cámara de Diputados — historial de reformas de la LFPDPPP: <https://www.diputados.gob.mx/LeyesBiblio/ref/lfpdppp.htm>
- EY México — boletín sobre la nueva LFPDPPP (publicación y cambios principales): <https://www.ey.com/es_mx/technical/tax/boletines-fiscales/nueva-ley-federal-proteccion-datos-personal-posesion-particulares>
