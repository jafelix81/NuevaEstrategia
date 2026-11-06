# Phase 151 — SEC Form 4: auditoría de semántica transaccional, propietarios y elegibilidad PIT

**Fecha:** 6 de noviembre de 2026  
**Estado:** auditoría de factibilidad completada; no se ejecutó un backtest de retornos.

## Decisión ejecutiva

Form 4 es una fuente condicionalmente útil para eventos de insiders, pero un panel ingenuo de “compras/ventas” clasificaría incorrectamente una parte material de los registros y podría duplicar operaciones.

La auditoría de dos trimestres reales confirma siete restricciones:

1. Los códigos P y S significan compra/venta en mercado abierto **o privada**. No demuestran ejecución en bolsa ni intención discrecional.
2. Table I contiene valores no derivados; Table II contiene derivados. Sus operaciones P/S no se deben sumar como compras/ventas de acciones ordinarias.
3. Un documento Form 4 puede incluir transacciones de tipo Form 5. Se deben conservar por separado.
4. Form 4/A es una presentación nueva con su propia hora de conocimiento; no se debe sumar sin reconciliar las líneas originales y modificadas.
5. REPORTINGOWNER se relaciona con las transacciones por ACCESSION_NUMBER, no por clave de línea. No existe una atribución plana y verificable de cada transacción a cada reporting owner.
6. AFF10B5ONE es un indicador a nivel de presentación, no una etiqueta por línea ni un clasificador general de operación discrecional.
7. FILING_DATE contiene solo fecha. El momento de conocimiento debe ser el timestamp real de aceptación de EDGAR.

**Decisión:** conservar Form 4 como fuente candidata de eventos conocidos al momento de presentación. No construir todavía una señal direccional con P/S. Primero hay que resolver acceptance timestamps, lineage de amendments, notas al pie, identidad de clase de acciones y cobertura histórica PIT.

## Fuente y reproducibilidad

Se reutilizó el artefacto original de Phase 39; no se descargó nuevamente información de la SEC.

- Artefacto GitHub Actions: 12781850078.
- SHA-256 del ZIP exterior: 203d7b1d2e29c999da318456af72e621cb30ef9a470d8f1610d088f9bebecb66.
- ZIP interior 2012Q1: 0cac6f943813dae94c20ecc8bca63fda692e2b8ac6d02ce2c322ab411f45c357.
- ZIP interior 2026Q3: a4e6a681cfcfa43a3d9e4ca9cfec1fd26a59d0a01eac7e9f7b5a0122092c90f3.

Se validaron los inventarios de tablas, claves únicas de presentación/transacción/propietario/nota al pie, joins por accession y referencias a footnotes. Las 20,991 parejas únicas de footnotes referenciadas en 2012Q1 y las 31,300 de 2026Q3 resolvieron contra FOOTNOTES; cero referencias quedaron huérfanas.

## Resultados de las muestras

Son dos muestras de extremo, no un análisis continuo de todos los trimestres.

| Métrica | 2012Q1 | 2026Q3 |
|---|---:|---:|
| Presentaciones Form 4 / 4-A | 63,678 | 34,148 |
| Form 4 originales | 61,816 | 33,521 |
| Form 4/A | 1,862 | 627 |
| Filas Table I no derivadas | 101,473 | 59,834 |
| Table I código P | 7,180 | 5,183 |
| Table I código S | 28,169 | 25,430 |
| Total Table I P/S | 35,349 | 30,613 |
| Table II derivadas P/S, separadas | 647 | 634 |
| P/S en presentaciones 4/A | 818 | 522 |
| P/S con TRANS_FORM_TYPE=5 | 253 | 42 |
| P/S con dirección A/D inconsistente | 133 | 82 |
| P/S con DEEMED_EXECUTION_DATE | 1,127 | 287 |
| P/S con alguna referencia a footnote | 21,300 (60.3%) | 26,168 (85.5%) |
| P/S dentro de accessions con varios reporting owners | 2,610 (7.4%) | 2,903 (9.5%) |
| Fecha de transacción posterior a FILING_DATE | 13 | 1 |

### Dirección y propiedad

- Código P representa 20.3% de P/S en 2012Q1 y 16.9% en 2026Q3; S representa el resto. Los conteos brutos no son una medida de convicción neta.
- Propiedad directa/indirecta: 27,662 directas y 7,687 indirectas en 2012Q1; 20,384 directas y 10,229 indirectas en 2026Q3. Propiedad indirecta puede involucrar trusts, cónyuges, sociedades u otras relaciones; no equivale necesariamente a una inversión personal en efectivo.
- 133/35,349 filas P/S (0.38%) en 2012Q1 y 82/30,613 (0.27%) en 2026Q3 no coinciden con la dirección adquirida/dispuesta esperada: P con A (acquired), S con D (disposed). Deben quedar en cuarentena.
- 112 filas P/S en 2012Q1 y 71 en 2026Q3 no reportan precio; en estas muestras todas reportan shares. Precio faltante no equivale a cero.

### Table I frente a Table II

Las instrucciones de la SEC distinguen Table I (valores no derivados) y Table II (derivados). Ejercicios y conversiones se informan en Table II, mientras que los valores subyacentes se informan separadamente en Table I. Las muestras contienen 647 y 634 operaciones P/S de Table II. Incluyen instrumentos como opciones, warrants, phantom stock, swaps, acciones preferentes u otros valores. No deben contarse como compras/ventas de acciones ordinarias ni interpretarse como bullish por el código P.

### Transacciones de tipo Form 5 dentro de Form 4

Las instrucciones permiten incluir transacciones Form 5 en una presentación Form 4 y permiten reportar anticipadamente determinadas operaciones que normalmente se informarían en Form 5. Hay 253 filas Table I P/S con TRANS_FORM_TYPE=5 en 2012Q1 y 42 en 2026Q3; 202 y 31 de ellas, respectivamente, tienen TRANS_TIMELINESS=E (early). Se deben mantener separadas de las filas de tipo 4.

El diccionario SEC define TRANS_TIMELINESS como E=Early, L=Late y vacío=On-time. En estas muestras de P/S dentro de presentaciones Form 4, 205 filas fueron early en 2012Q1 y 36 en 2026Q3; no hubo L. No se debe deducir cumplimiento legal únicamente del desfase de días calendario.

### Amendments y edad del evento

Una presentación 4/A puede agregar líneas o modificar líneas existentes; no debe repetir líneas sin cambios. Por eso una 4/A es nueva información en su propia aceptación, no una segunda operación que se deba sumar ni una razón para retrofechar una versión corregida.

El desfase calendario FILING_DATE menos TRANS_DATE de Table I P/S:

| Estadístico | 2012Q1 | 2026Q3 |
|---|---:|---:|
| Mediana | 2 días | 2 días |
| Percentil 90 | 4 días | 4 días |
| Percentil 95 | 11 días | 5 días |
| Percentil 99 | 344.5 días | 51 días |
| Máximo | 3,959 días | 7,308 días |
| Más de 365 días | 309 filas | 65 filas |

Son diferencias de fecha calendario, no un cálculo de plazo legal ni un sustituto de TRANS_TIMELINESS. La cola extrema y las 14 fechas de transacción posteriores a FILING_DATE (13 en 2012Q1, una en 2026Q3) requieren cuarentena y revisión del filing original. En un panel predictivo, el conocimiento empieza en la aceptación EDGAR; la antigüedad del evento debe mantenerse como atributo explícito. Nunca retrofechar el conocimiento a TRANS_DATE.

### Presentaciones conjuntas y atribución del propietario

La clave de REPORTINGOWNER es (ACCESSION_NUMBER, RPTOWNERCIK); la de Table I es (ACCESSION_NUMBER, NONDERIV_TRANS_SK). No existe una clave plana transacción-propietario. Las instrucciones permiten presentaciones conjuntas/de grupo y transacciones de valores pertenecientes por separado a distintos propietarios. Por ello, las tablas planas no demuestran qué reporting owner corresponde a cada línea.

- Accessions P/S con más de un reporting owner: 749 en 2012Q1 y 580 en 2026Q3.
- Filas P/S dentro de esos accessions: 2,610 y 2,903.

No expandir cada transacción por cada reporting owner. Eso multiplica el volumen y fabrica clusters de insiders. Hasta que la fuente establezca la atribución por línea, usar eventos a nivel de accession y marcar la atribución del propietario como ambigua. No contar automáticamente una presentación conjunta como varias operaciones independientes.

### AFF10B5ONE y footnotes

AFF10B5ONE no existe en el esquema 2012Q1; todos los casos de ese periodo son **unknown**, no false. En 2026Q3, los accessions P/S se dividen en 4,859 con checkbox true y 8,099 false. El campo está en SUBMISSION y se relaciona por accession, no por línea de transacción. No debe copiarse a cada línea de una presentación con múltiples operaciones como si fuera una clasificación individual.

La SEC exige indicar la operación bajo Rule 10b5-1(c) y la fecha de adopción del plan en la explicación de respuestas; el checkbox aplica a presentaciones desde el 1 de abril de 2023. La ausencia previa no significa ausencia de plan, y false no prueba intención discrecional. En la muestra 2012Q1, 8,486 filas P/S tienen footnotes referenciadas cuyo texto contiene “10b5”; en 2026Q3 son 13,077. Son coincidencias de palabras en notas vinculadas, no etiquetas adjudicadas de plan. Demuestran por qué no se puede convertir el esquema anterior a 2023 en un grupo limpio sin planes.

Los conteos de palabras clave (plan/automatic, weighted average, trust, tax, options, private, open market) son diagnósticos, no etiquetas automáticas. P/S continúa significando mercado abierto **o privado** bajo las instrucciones oficiales; que una nota no diga “private” no demuestra que haya sido una operación bursátil.

## Reglas PIT para cualquier panel futuro

1. Usar el timestamp de aceptación EDGAR por accession como primer momento de conocimiento. FILING_DATE es fecha solamente; PERIOD_OF_REPORT es fecha del evento.
2. Para aceptaciones fuera de horario, la primera sesión operable es la siguiente. Para aceptaciones intradía, respetar la hora real y el calendario de mercado.
3. Mantener Form 4 original y cada 4/A como registros inmutables. Una enmienda se conoce únicamente desde su aceptación. Reconciliar accession original y líneas enmendadas antes de calcular actividad neta.
4. Table I P/S es solo candidato. Poner en cuarentena dirección A/D inconsistente, tipo de transacción distinto, eventos muy antiguos, precio faltante y notas/operaciones privadas ambiguas hasta revisar el filing original.
5. Mantener Table II separada e identificar instrumento, subyacente y términos antes de cualquier mapeo direccional.
6. Conservar checkbox 10b5-1, fecha de adopción y footnotes como procedencias separadas. False no equivale a discrecional; ausencia pre-2023 no equivale a false.
7. Mantener propiedad directa/indirecta separada. No duplicar transacciones por número de reporting owners.
8. Resolver issuer CIK hacia identificador efectivo de clase/valor. El ticker declarado por emisor no es suficiente; conservar símbolo y CIK originales.
9. Para la señal, usar la primera sesión operable después de la aceptación. Si se acepta después del cierre, no usarla hasta la sesión siguiente.
10. Comparar cualquier feature de eventos/clusters incrementalmente frente a LTM/F80 congelado, con exposición y costos idénticos, splits cronológicos, bootstrap/LOO y holdout realmente intacto.

## Fuentes oficiales

- SEC, [Insider Transactions Data Sets](https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets).
- SEC, [Insider Transactions Data Sets README](https://www.sec.gov/files/insider_transactions_readme.pdf): tablas, claves, códigos, timeliness, estructura y limitaciones.
- SEC, [Form 4 instructions](https://www.sec.gov/files/form4data.pdf): plazo, Table I/II, presentaciones conjuntas, códigos, amendments y checkbox Rule 10b5-1.
- SEC, [Section 16 interpretations](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/exchange-act-section-16-related-rules-forms).

## Próximo gate

**Promover solo a investigación condicional de eventos conocidos al presentar. No promover todavía una señal P/S.** El siguiente paso factible es reconciliar acceptance timestamps y lineage de amendments sobre la muestra Phase 39; después, ampliar a una muestra estratificada de trimestres y medir cobertura issuer/share-class frente a un universo histórico survivorship-aware. Solo entonces preregistrar clusters de compras de insiders y probar retornos futuros.

No se ejecutó backtest, no se consumió el holdout final, no se contactó ni compró información a proveedores, y no se modificó producción. F80_TOP20_PARTIAL50_BASELINE_C20 permanece congelado.
