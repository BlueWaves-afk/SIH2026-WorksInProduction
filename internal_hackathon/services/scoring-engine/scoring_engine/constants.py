"""Weights, band cutoffs and guarantees.

Signal model v2 — aligned to ICAR-CRIDA's Farmers' Distress Index (FDI).
See design/signal_model_fdi_aligned.md.

    final_score = clamp(shock_score * vulnerability_multiplier, 0, 100)
"""

MODEL_VERSION = "rules-fdi-0.2.0"
SCORE_DISCLAIMER = "This is not a credit, loan-default, or insurance score."

# --- FDI alignment ------------------------------------------------------------
# CRIDA scores 0-1 with bands <0.5 low / 0.5-0.7 moderate / >0.7 severe.
# We use the same scale x100 and the SAME cutoffs, so our Red == CRIDA "severe".
FDI_SCALE = 100
BAND_AMBER_MIN = 50   # CRIDA 0.5 - moderate distress
BAND_RED_MIN = 70     # CRIDA 0.7 - severe distress

# --- Shock signals (acute) -> shock_score 0-100 -------------------------------
# FDI D1 exposure to risk
W_S1_RAINFALL_DEFICIT = 20
W_S2_RAINFALL_EXCESS = 10
W_S3_SATELLITE_CROP_STRESS = 15     # NDVI/NDWI anomaly - direct observation
W_S4_PEST_PRESSURE = 8
# FDI D2 debt
W_S5_REPAYMENT_WINDOW = 20          # opt-in only, coarse bands
# FDI D6 triggers
W_S13_PRICE_SHOCK = 20              # incl. below-MSP flag
W_S14_ACUTE_REPORT = 7

SHOCK_TOTAL = (W_S1_RAINFALL_DEFICIT + W_S2_RAINFALL_EXCESS + W_S3_SATELLITE_CROP_STRESS
               + W_S4_PEST_PRESSURE + W_S5_REPAYMENT_WINDOW + W_S13_PRICE_SHOCK
               + W_S14_ACUTE_REPORT)
assert SHOCK_TOTAL == 100, f"shock weights must total 100, got {SHOCK_TOTAL}"

# --- Vulnerability signals (structural) -> multiplier 0.7-1.3 -----------------
VULN_MIN = 0.7
VULN_MAX = 1.3
VULN_BASE = 1.0

# FDI D3 adaptive capacity
ADJ_S6_NO_SCHEME_COVER = +0.10      # not enrolled in PMFBY/PM-Kisan/KCC
ADJ_S6_SCHEME_COVERED = -0.10
ADJ_S7_POOR_INSTITUTIONAL_ACCESS = +0.05
# FDI D4 land holding + irrigation
ADJ_S8_MARGINAL_HOLDING = +0.10     # <1 ha
ADJ_S8_LARGE_HOLDING = -0.05        # >2 ha
ADJ_S9_RAINFED = +0.10
ADJ_S9_ASSURED_IRRIGATION = -0.10
# FDI D5 sensitivity / mitigation
ADJ_S10_CRITICAL_GROWTH_STAGE = +0.10
ADJ_S11_MONOCROP = +0.05            # no contingency/secondary crop
ADJ_S12_POOR_SOIL_RETENTION = +0.05

# --- Reliability ---------------------------------------------------------------
HYSTERESIS_OBSERVATIONS = 2         # corroborating observations before a band change
HYSTERESIS_DAYS = 3
CONFIDENCE_FLOOR = 0.45             # below this -> suppress escalation (never guess)

# --- Privacy firewall ----------------------------------------------------------
# Fields that must never influence the score (masterspec 4.5).
BANNED_FIELDS = frozenset({"aadhaar", "bank_account", "lender_id", "credit_score"})

# FDI D7 (socio-psychological) is collected by CRIDA via trained human interview.
# We deliberately DO NOT score it - S15 is an officer-side context flag only.
# See design/signal_model_fdi_aligned.md section 5.
D7_IS_SCORED = False
