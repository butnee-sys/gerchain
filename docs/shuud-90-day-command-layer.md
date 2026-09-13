# SHUUD 90-day Sandbox Command Layer

## Purpose

Turn durable SHUUD sandbox measurements into a production-readiness decision surface.

The command layer is **read-only** over persisted KPI/economic evidence. It does not
create incidents, change SHIID decisions, authorize settlement release, or write
economic measurements.

## Decision gate

The gate evaluates two observed dimensions:

1. **Operational:** share of measured cases cleared within 120 seconds.
2. **Economic evidence:** share of cases with persisted `shuud-economic-v1`
   measurement.

The default policy thresholds are configurable in `GateThresholds`:

- minimum cases: 30
- GO: at least 95% within 120 seconds and at least 90% economic coverage
- CONDITIONAL GO: at least 80% within 120 seconds and at least 75% economic coverage
- otherwise: NO-GO

These thresholds are policy parameters, not monetary assumptions.

## API

- `GET /api/v1/shuud/sandbox/command`
- `GET /api/v1/shuud/sandbox/command/weekly`
- `GET /api/v1/shuud/sandbox/command/daily`

The response contains the decision, configured gate, observed KPIs, the existing
KPI payload, and a one-line decision statement.

## One-line decision

> Хэдэн case дээр, хэдэн секунд хэмнэж, хэдэн төгрөгийн хэмжигдсэн өгөөж бий болгосон бэ?

The monetary values come from the existing persisted economic measurements; the
command layer never invents or recomputes them.
