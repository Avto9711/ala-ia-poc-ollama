# COOPNAMA RAG Test Questions

Use these prompts to validate that the agent retrieves grounded answers from `coopnama-servicios.pdf` instead of answering from generic model knowledge.

## Direct Retrieval

- `¿Cuál es el monto mínimo mensual para afiliarse al Ahorro Turístico Cooperativo (TURICOOP)?`
- `¿Qué interés gana el ahorro navideño NAVICOOP y cuándo se entrega ese dinero?`
- `¿Cuál es el depósito mínimo para abrir un certificado de depósito cooperativo?`
- `¿Desde cuándo un socio puede solicitar un préstamo gerencial?`
- `¿Cuál es la tasa del préstamo normal y cuál es su plazo máximo?`
- `¿Qué porcentaje del sueldo neto puede afectar un socio al usar uno o más servicios?`
- `¿Cuál es el monto mínimo y máximo del préstamo rápido cooperativo?`
- `¿Cuál es el plazo máximo para pagar el préstamo rápido cooperativo?`
- `¿Qué tasa se cobra para vehículos 0 kilómetro?`
- `¿Qué condición deben cumplir los vehículos usados para ser financiados?`

## Eligibility And Rules

- `¿Qué se necesita para tener derecho a un préstamo de inversión?`
- `¿Cuántas cuotas nominales mínimas se requieren para solicitar un préstamo de inversión?`
- `¿Qué se requiere para obtener un préstamo expreso?`
- `¿El préstamo expreso exige tener Ahorro Retirable?`
- `¿Quiénes pueden incluirse en el servicio de ayuda mutua?`
- `¿Qué límite de edad aplica para ingresar padres o madres al servicio de ayuda mutua?`
- `¿Qué proyectos prioriza el servicio de préstamo para emprendimiento?`
- `¿Qué tipos de proyectos quedan excluidos del préstamo para emprendimiento?`

## Procedures

- `¿Qué documentos piden para solicitar un préstamo hipotecario para vivienda?`
- `¿Qué debe llevar un socio para solicitar un préstamo normal?`
- `¿Qué documentos debe presentar un socio administrativo al solicitar un préstamo normal?`
- `¿Cómo se cancela un certificado de depósito cooperativo antes de su vencimiento?`
- `¿Cuál es el procedimiento para ingresar al servicio de ahorro retirable?`
- `¿Cómo es el procedimiento para retirar ahorro retirable?`

## Claims And Benefits

- `¿Qué cubre el servicio de autoprotección cuando fallece un socio?`
- `¿Qué deudas no cubre la autoprotección?`
- `¿Qué documentos se necesitan para reclamar el beneficio de autoprotección por un socio fallecido?`
- `¿Qué documentos se necesitan para reclamar ayuda mutua?`
- `¿Cómo se reclama el servicio de crédito funerario?`

## Multi-Fact Prompts

- `Resume las condiciones del préstamo rápido cooperativo: monto, tasa, plazo y forma de pago.`
- `Compárame el préstamo gerencial y el préstamo normal en requisitos iniciales, tasa y plazo máximo.`
- `Compárame NAVICOOP y TURICOOP en monto mínimo, intereses y uso del ahorro.`
- `Explícame las reglas principales del ahorro retirable, incluyendo depósito inicial, saldo mínimo y retiros.`

## Retrieval-Specific Checks

- `¿Qué pago único no reembolsable se descuenta al primer depósito del ahorro retirable?`
- `¿Qué porcentaje de los intereses se dedica a la autoprotección?`
- `¿Qué descuento obtiene un socio que usa ahorro turístico para apalancar el crédito en COOPMARENA?`
- `¿Qué porcentaje del préstamo de farmacia puede comprometer del sueldo neto y en cuántas cuotas se paga?`
- `¿Cuál es el monto máximo del servicio óptico y qué pasa si el crédito excede ese monto?`

## Mixed Routing

- `¿Qué interés paga NAVICOOP y cuál es el nombre del objeto 7 de restful-api.dev?`
- `Según COOPNAMA, ¿qué se necesita para un préstamo expreso? Además, busca el objeto 10 en restful-api.dev.`
- `Compárame los requisitos para ser Presidente según la Constitución y los requisitos para solicitar un préstamo normal en COOPNAMA.`

## Boundary Tests

- `¿Cuál es la dirección de una oficina de COOPNAMA?`
- `¿Cuál es la tasa exacta actual del mercado para TURICOOP?`
- `¿Qué cubre el seguro médico de COOPNAMA?`

Expected behavior for the boundary tests:

- the agent should say the PDF does not provide enough support if the answer is not grounded in `coopnama-servicios.pdf`
- the agent should avoid inventing missing facts
