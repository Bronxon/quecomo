# 11 · Validación del producto y modelo de negocio

> Este documento separa **lo que sabemos** de **lo que suponemos**. El MVP demuestra que la regla de confianza se puede construir; **no** demuestra todavía que las personas la quieran usar ni que el modelo sea sostenible.

## 1. Resumen ejecutivo

¿Qué Como? propone resolver dos problemas: la **dispersión de información** al elegir restaurante y la **baja confianza** en las reseñas. La propuesta es técnicamente viable (este repositorio lo demuestra), pero su valor depende de supuestos aún no validados: que los clientes registren sus consumos, que los restaurantes confirmen esas transacciones y que esa «verificación» cambie realmente la decisión de los usuarios.

## 2. Hechos, supuestos y evidencia

| Afirmación | Tipo | Evidencia actual |
|---|---|---|
| La información para elegir restaurante está dispersa | Supuesto razonable del equipo | Experiencia propia; falta entrevistar usuarios |
| Las personas desconfían de las reseñas en línea | Supuesto | Falta evidencia del segmento objetivo |
| Una reseña ligada a una transacción genera más confianza | **Supuesto central** | Ninguna |
| Los clientes registrarán sus transacciones en la app | **Supuesto crítico** | Ninguna |
| Los restaurantes confirmarán y completarán transacciones | **Supuesto crítico** | Ninguna |
| Es posible construir la regla de confianza de forma fiable | Hecho (técnico) | Este MVP y sus 110 pruebas |

## 3. Supuestos de mayor riesgo (priorizados)

| # | Supuesto | Si es falso… | Riesgo |
|---|---|---|---|
| S1 | El cliente está dispuesto a registrar su consumo | No hay transacciones → no hay evaluaciones → no hay ranking | 🔴 Muy alto |
| S2 | El restaurante confirma y completa en tiempo razonable | Las transacciones se quedan PENDIENTES y nadie puede evaluar | 🔴 Muy alto |
| S3 | El restaurante no bloquea a clientes insatisfechos | El ranking pierde credibilidad (sesgo positivo) | 🔴 Alto |
| S4 | «Evaluación respaldada por transacción» cambia la decisión del usuario | El diferenciador no aporta valor percibido | 🟠 Alto |
| S5 | Hay suficientes restaurantes en una zona para que comparar sea útil | Problema de arranque en frío de un mercado de dos lados | 🟠 Alto |
| S6 | Alguien pagará (restaurantes, usuarios o anunciantes) | El modelo no es sostenible | 🟡 Medio (posterior) |

## 4. Riesgo crítico: el locatario controla la evidencia

En el MVP, **solo el locatario** confirma y completa transacciones. Esto protege contra que un cliente se habilite a sí mismo, pero crea un incentivo perverso: un restaurante podría **no completar** las transacciones de clientes que tuvieron una mala experiencia.

Mitigaciones a evaluar (no implementadas aún):

| Opción | Cómo funciona | Ventaja | Desventaja |
|---|---|---|---|
| **Confirmación automática con plazo** | Si el restaurante no rechaza en N horas con motivo, la transacción pasa a COMPLETADA | Quita al restaurante el poder de bloquear en silencio | Un cliente podría declarar consumos falsos |
| **Código de ticket / QR** | El restaurante imprime un código único en el ticket; el cliente lo captura | Evidencia objetiva, sin intervención manual | Requiere que el restaurante adopte el proceso |
| **Integración con punto de venta** | La transacción llega desde el sistema de cobro | Evidencia fuerte | Costosa; depende de cada proveedor |
| **Disputa** | El cliente puede impugnar una transacción no completada; modera el administrador | Equilibra el poder | Carga operativa de moderación |
| **Métrica pública** | Mostrar el % de transacciones que cada restaurante completa | Desincentiva el bloqueo | No lo impide |

Recomendación: probar primero **código de ticket + disputa**, que es lo de menor costo y mayor aprendizaje.

## 5. Cliente objetivo y propuesta de valor

**Segmento inicial sugerido** (a validar): personas que salen a comer en una zona concreta de una ciudad, con presupuesto definido, que hoy combinan mapas y redes sociales para decidir; y restaurantes pequeños o medianos de esa misma zona que no tienen presencia digital propia.

| | Cliente | Restaurante |
|---|---|---|
| **Trabajo por hacer** | Decidir rápido dónde comer según precio, distancia y horario | Atraer clientes y conocer su opinión real |
| **Frustraciones** | Fuentes dispersas; reseñas poco confiables | Reseñas falsas o de quien nunca fue |
| **Ganancias** | Comparación en un solo lugar; reseñas con respaldo | Perfil propio actualizado; evaluaciones de clientes reales |
| **Cómo lo resuelve el MVP** | Búsqueda con 8 filtros, comparación, ficha completa | Panel del locatario, menú, promociones, evaluaciones recibidas |

## 6. Modelo de negocio (Lean Canvas preliminar)

| Bloque | Hipótesis |
|---|---|
| Problema | Información dispersa; reseñas sin trazabilidad |
| Segmentos | Comensales de una zona urbana; restaurantes pequeños y medianos |
| Propuesta única de valor | «Reseñas solo de quien realmente consumió» |
| Solución | Búsqueda + comparación + evaluación respaldada por transacción |
| Canales | Restaurantes que invitan a sus clientes (código en el ticket), redes sociales locales |
| Fuentes de ingreso (opciones a validar) | Suscripción para restaurantes con funciones avanzadas; promociones destacadas **claramente identificadas como patrocinadas** |
| Estructura de costos | Desarrollo, alojamiento, moderación, adquisición de restaurantes |
| Métricas clave | Ver sección 8 |
| Ventaja difícil de copiar | Base de evaluaciones con historial verificable (se construye con el tiempo) |

> ⚠️ No se incluyen cifras de mercado ni proyecciones financieras porque no hay datos que las respalden. Deben construirse con la información que arrojen los experimentos.

> ⚖️ Cualquier resultado patrocinado debe distinguirse claramente de los orgánicos y **no** debe alterar las calificaciones; de lo contrario se destruye el diferenciador y se generan riesgos legales (ver [10](10_cumplimiento_legal.md)).

## 7. Plan de experimentación (bajo costo, alto aprendizaje)

| # | Experimento | Supuesto | Métrica | Criterio de éxito (a acordar por el equipo) |
|---|---|---|---|---|
| E1 | 10–15 entrevistas a comensales sobre cómo eligen restaurante | S4 | Menciones espontáneas de desconfianza en reseñas | Definir umbral antes de entrevistar |
| E2 | 5–8 entrevistas a dueños de restaurantes | S2, S3, S6 | Disposición a confirmar transacciones o imprimir un código | Definir umbral antes de entrevistar |
| E3 | Prueba de usabilidad del MVP con 5 personas (tareas guiadas) | S1 | % que completa «registrar transacción» sin ayuda; tiempo | Definir umbral |
| E4 | Piloto «concierge» con 2–3 restaurantes durante 2 semanas | S1, S2 | % de transacciones completadas; tiempo medio a COMPLETADA; % de evaluaciones por transacción | Definir umbral |
| E5 | Prueba A/B de la ficha: con y sin la marca «respaldada por transacción» | S4 | Preferencia declarada / restaurante elegido | Definir umbral |

Regla: fijar el criterio de éxito **antes** de cada experimento y registrar resultados y decisiones (perseverar, ajustar o pivotar) en este documento.

## 8. Indicadores

| Indicador | Qué mide | Fórmula |
|---|---|---|
| Tasa de completitud | Salud del flujo de confianza | Transacciones COMPLETADAS / registradas |
| Tiempo a completar | Fricción del restaurante | Mediana (COMPLETADA − registro) |
| Tasa de evaluación | Participación | Evaluaciones / transacciones COMPLETADAS |
| Tasa de cancelación por restaurante | Posible sesgo (S3) | Canceladas por el locatario / registradas |
| Cobertura | Utilidad de comparar | Restaurantes activos por zona |
| Retención | Valor recurrente | Usuarios que vuelven a buscar en 30 días |

El MVP ya registra los datos para calcular las cuatro primeras (estados e historial de cada transacción).

## 9. Plan de acción priorizado

1. Ejecutar E1 y E2 (no requieren desarrollo).
2. Con los resultados, decidir el mecanismo contra el sesgo del locatario (sección 4).
3. Agregar persistencia y autenticación (requisitos para cualquier piloto real).
4. Ejecutar E3 con el MVP actual y E4 con restaurantes reales.
5. Revisar este documento con la evidencia obtenida antes de invertir en monetización.
