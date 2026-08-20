from datetime import date
from typing import Dict, Any, List

class ScoringEngine:
    def __init__(self):
        pass

    def calculate_score(self, farmer_profile: dict, weather_data: dict, market_data: dict, repayment_opt_in: dict = None) -> dict:
        score = 0
        drivers = []
        confidence = 1.0

        # 1. Rainfall Shock (0-35)
        if weather_data:
            if weather_data.get('ttl', 0) < 0:
                confidence -= 0.3 # Stale data lowers confidence
            else:
                dev = weather_data.get('value', 0)
                if dev < -20:
                    points = 25
                    if farmer_profile.get('irrigation_type') == 'rainfed':
                        points = 35
                    score += points
                    drivers.append(f"Rainfall {dev}%")
        
        # 2. Market Stress (0-30)
        if market_data:
            dev = market_data.get('deviation_pct', 0)
            if dev < -15:
                score += 30
                drivers.append(f"{market_data.get('commodity')} {dev}%")

        # 3. Repayment Window (0-20)
        if repayment_opt_in and repayment_opt_in.get('is_due_soon'):
            score += 20
            drivers.append("Loan due soon")

        # Suppress escalation if confidence is too low
        if confidence < 0.8:
            # Cap the score so it doesn't trigger Red
            score = min(score, 59)

        # Determine Band
        if score < 30:
            band = 'Green'
        elif score < 60:
            band = 'Amber'
        else:
            band = 'Red'

        return {
            'score': score,
            'band': band,
            'confidence': round(confidence, 2),
            'drivers': drivers[:3]
        }

