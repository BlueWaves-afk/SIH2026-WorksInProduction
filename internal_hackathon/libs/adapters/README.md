# Module 3 — Ingestion & Government Adapters

IMD, Agmarknet/eNAM, AgriStack (API Setu), Bhashini, Bhuvan adapters + the 90-day replay fixtures.

**Spec:** [`design/module_3_ingestion_adapters.md`](../../design/module_3_ingestion_adapters.md)

## Boundary

The **only** module that talks to external services. Every source has a Mock and a Real implementation behind one interface.

## Shared contracts

Import cross-module types from `services/platform-core/app/schemas/` — never redefine them.

## Status

Core contracts are runnable: `AdapterRegistry`, `HealthTracker`, `TTLPolicy`, `QualityGate`,
raw-payload normalisation, and deterministic replay scenarios. Source-specific Mock/Real clients
remain isolated scaffolds and must be implemented behind these interfaces; no live credentials are
needed for the current tests.
