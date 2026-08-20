# Module 7 — AI & Agentic Copilot Layer

Officer copilot (agentic + scheme RAG), farmer voice copilot, LLM explainer, guardrails, shadow ML.

**Spec:** [`design/module_7_ai_copilot.md`](../../design/module_7_ai_copilot.md)

## Boundary

**Read-only against the score.** Human approves every outward action. Citations required. Never mutates M4 output.

## Shared contracts

Import cross-module types from `services/platform-core/app/schemas/` — never redefine them.

## Status

First deterministic M7 slice implemented: template-first briefs, fixed playbook, citation/expiry/consent
guardrails, PII redaction, prompt-injection sanitisation and tests. LLM/RAG/voice HTTP integration remains
unbuilt until its upstream contracts are available. See the root `tasks.md` for verified build output.
