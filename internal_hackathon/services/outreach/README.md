# Module 9 — Outreach Automation & Channel Strategy

Owns the **daily cycle** (the clock nothing else owned) and the **channel strategy**.
Decides *whether, when and by which channel* to reach a farmer; M6 does the sending.

**Spec:** [`design/module_9_outreach_automation.md`](../../design/module_9_outreach_automation.md)

## The premise

> A farmer will never open our site. The farmer does nothing; **the phone rings.**

## Channel ladder (by reach, not richness)

`SMS (1) → IVR/voice (2) → WhatsApp (3) → PWA push (4)` · **email = officers only**

SMS and IVR reach any phone with no internet; IVR needs no literacy.
Red band dispatches SMS **and** IVR in parallel.

## App-free return paths

Missed call (free callback) · IVR keypress · SMS reply — each becomes a `farmer_report`
Observation and can open an officer case.
