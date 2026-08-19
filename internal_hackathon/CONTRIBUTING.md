# Working in parallel

## Ground rules

1. **Contracts first.** Cross-module types live in `services/platform-core/app/schemas/`.
   Changing one is a cross-team decision — open a PR that tags every affected module owner.
2. **Own your directory.** Each module owns exactly one top-level folder. Do not edit
   another module's internals; call its public interface or mock it.
3. **Mock the other side.** Every module must be developable and testable alone.
   M3 ships mock adapters, M6 ships mock providers, M4 is pure and needs nothing.
4. **Follow your spec.** `design/module_N_*.md` is the contract with the rest of the team.
   If reality diverges, update the spec in the same PR.

## Branching

`main` ← `module-N/<short-topic>` (e.g. `module-4/rainfall-rules`).
Small PRs. Keep the demo path green.

## Definition of done (per module)

- [ ] Public interface matches the spec's §6
- [ ] Unit tests for the spec's §11 acceptance criteria
- [ ] Works against mocks/fixtures with zero live credentials
- [ ] README updated if the interface changed

## Non-negotiable guardrails

- No Aadhaar / bank / lender identifiers anywhere. Ever.
- The score is **deterministic rules only** — no model in the safety path (M4).
- AI never sends anything outward without human approval (M7 → M6).
- Stale data lowers confidence; it must never manufacture an alert.
