# Internal problem-statement inventory and provenance

**Source artifact:** [`SIH Problem Statements.docx`](SIH%20Problem%20Statements.docx)<br>
**SHA-256:** `91f7666fecbb890ea373b21168def98436f7582bfa720191d8a6ff99a108d083`<br>
**Reviewed:** 19 August 2026<br>
**Status:** institute-level SIH-styled source; official national SIH 2026 mapping pending verification

## What this document is

The DOCX itself calls the event **“INTERNAL HACKATHON 2026”**, describes the set as **“Modeled on
Smart India Hackathon (SIH) format & 2026 official themes,”** and contains five software and two
hardware statements. It is therefore a valid internal-round brief, but it is not an official SIH
national problem-statement publication or proof that these identifiers/titles will be accepted by
the national portal.

Before external submission, the college SPOC should export the official PS record from the
authenticated SIH portal and reconcile: PS ID, title, organization, category, theme, exact wording,
datasets, contact person, deliverables, and any restrictions. Keep the official export as a separate,
dated artifact; do not overwrite this institute source.

## Current release-status check

As of this review, the public [SIH homepage](https://www.sih.gov.in/) shows past-edition navigation
through SIH 2025 and states that institutes may use institute- or societal-level problems for their
internal hackathon without waiting for the national launch. The official [MoE Innovation Cell
announcement](https://www.linkedin.com/posts/moe-innovation-cell_sih2026-smartindiahackathon-activity-7480524362941456384-Whuz)
announced SIH 2026 SPOC registration and said institutions would receive access to problem statements
upon launch. I could not verify a publicly accessible national SIH 2026 roster from the public
homepage at the time of review. Treat the authenticated SPOC portal as authoritative.

## Inventory

| ID | Statement | Mode | Internal-round core loop | Main system risk |
|---|---|---|---|---|
| PS-01 | AI mental-health and wellness companion for students | Software | Check-in → safe, non-diagnostic support → human/helpline escalation → aggregate-only analytics | Clinical safety, false negatives, privacy, and counsellor capacity |
| PS-02 | Smart crop advisory and farmer-distress early warning | Software | Weather/price/farmer signals → explainable support-priority score → local-language action → officer case closure | Crowded advisory space, sensitive repayment signal, dirty feeds, and adoption evidence |
| PS-03 | Tamper-proof academic credential verification | Software | Institution issue → signed/hash credential + QR → verifier checks → revocation status | Blockchain overengineering, key custody, privacy, and revocation semantics |
| PS-04 | Space-debris tracking and satellite collision-risk dashboard | Software | Public orbital data → propagate/screen conjunctions → uncertainty-aware triage → analyst review | TLE uncertainty, false confidence, data licensing, and indirect user impact |
| PS-05 | Disaster early-warning and resource coordination | Software | Authoritative alert + field report → incident triage → compatible resource assignment → closure/audit | Duplicate alerting systems, spoofed reports, offline operations, and dispatch liability |
| PS-06 | Low-cost IoT smart helmet | Hardware | Impact sensor → crash decision → GPS/GSM alert → false-alarm cancellation | Sensor calibration, false triggers, cellular coverage, battery and enclosure safety |
| PS-07 | Drone crop-health spotting and targeted spraying | Hardware | RGB capture → candidate stress hotspot → human approval → metered water/spray demo | Drone permissions, drift/chemical safety, agronomic validity, payload and flight reliability |

## Selection and architecture implications

PS-02 remains the selected internal system because it supports a strong software-only vertical slice:
replayable data, deterministic scoring, a named officer user, multilingual farmer UX, and a visible
case-closure outcome. It also permits an honest demo with fixtures when government credentials are not
available.

The architecture should not be allowed to expand merely because the source document lists ambitious
outcomes. The internal MVP must remain:

`fixture → adapter → score → RiskEvent → AlertCase → officer action → farmer status`

Live Bhashini, telecom delivery, AgriStack/API Setu credentials, external LLM calls, ML challengers,
and all-India rollout are integration or pilot work. They may be shown as adapter contracts and
stretch paths, but they must not be prerequisites for a deterministic judged replay.

## Senior-engineering review of all seven statements

- **PS-01:** viable only with a clinical advisor, deterministic crisis override, explicit consent,
  human ownership, and no claim of diagnosis or therapeutic efficacy.
- **PS-02:** strongest current fit for this team’s software architecture; the product must be a
  support radar and officer workflow, not another chatbot or credit score.
- **PS-03:** use signed credentials and a verifiable append-only log first; a permissioned blockchain
  is not justified for the internal MVP unless the issuing authority requires it.
- **PS-04:** position as screening/triage, never operational collision probability or maneuver advice;
  public TLE data needs age, provenance, and uncertainty on every event.
- **PS-05:** do not duplicate SACHET/IMD alert dissemination; own the post-alert operations queue,
  resource matching, approval gate, and audit trail.
- **PS-06:** validate detection and alert reliability with repeatable impact fixtures; separate a
  lab demonstrator from road-safety certification claims.
- **PS-07:** demonstrate water/food-dye targeting with a ground-rig fallback; real pesticide use and
  flight operations require the relevant permissions, trained operators, and agronomic controls.

## Decision log

| Decision | State |
|---|---|
| Use the DOCX as the internal-round source of truth | Accepted for internal hackathon planning |
| Claim it is the official SIH 2026 national list | Rejected pending authenticated SPOC verification |
| Continue PS-02 architecture work | Accepted |
| Build live external integrations before replay | Rejected |
| Preserve source DOCX unchanged | Accepted; checksum recorded above |
