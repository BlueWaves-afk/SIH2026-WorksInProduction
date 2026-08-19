# Module 7 — AI & Agentic Copilot Layer

Officer copilot (agentic + scheme RAG), farmer voice copilot, LLM explainer, guardrails, shadow ML.

**Spec:** [`design/module_7_ai_copilot.md`](../../design/module_7_ai_copilot.md)

## Boundary

**Read-only against the score.** Human approves every outward action. Citations required. Never mutates M4 output.

## Shared contracts

Import cross-module types from `services/platform-core/app/schemas/` — never redefine them.

## Status

Scaffolded. See the spec's §11 for acceptance criteria and §12 for the MVP boundary.
