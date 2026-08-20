from datetime import date
from typing import Dict, Any, List

class ScoringEngine:
    def __init__(self):
        pass

    def calculate_vulnerability_multiplier(self, profile: dict) -> float:
        multiplier = 1.0
        # Irrigation vulnerability
        if profile.get('irrigation_type') == 'rainfed':
            multiplier += 0.3
        
        # Land size vulnerability
        area = profile.get('area_band')
        if area == '<1 ha':
            multiplier += 0.2
        elif area == '1-2 ha':
            multiplier += 0.1
            
        # Crop stage vulnerability (simplified for MVP)
        # Assuming cotton is highly vulnerable 60 days after sowing
        if profile.get('crop') == 'cotton':
            multiplier += 0.2
            
        return multiplier

    def calculate_score(self, farmer_profile: dict, weather_data: dict, market_data: dict, repayment_opt_in: dict = None, farmer_report: dict = None) -> dict:
        score = 0
        drivers = []
        confidence = 1.0

        # Calculate base vulnerability multiplier (Shock x Vulnerability)
        vuln_mult = self.calculate_vulnerability_multiplier(farmer_profile)

        # 1. Rainfall / Forecast Shock (Max 35)
        if weather_data:
            if weather_data.get('ttl', 0) < 0:
                confidence -= 0.3 # Stale data lowers confidence
            else:
                dev = weather_data.get('value', 0)
                if dev < 0:
                    # Shock x Vulnerability
                    raw_points = abs(dev) * vuln_mult
                    points = min(35, raw_points) # Cap at 35
                    if points > 10:
                        score += points
                        drivers.append(f"Rainfall {dev}%")
        
        # 2. Market Stress (Max 30)
        if market_data:
            dev = market_data.get('deviation_pct', 0)
            if dev < 0:
                # Market stress hits marginal farmers harder
                raw_points = abs(dev) * vuln_mult
                points = min(30, raw_points)
                if points > 10:
                    score += points
                    drivers.append(f"{market_data.get('commodity')} {dev}%")

        # 3. Optional Repayment Window (Max 20)
        if repayment_opt_in and repayment_opt_in.get('is_due_soon'):
            score += 20
            drivers.append("Loan due soon")
            
        # 4. Crop/Soil static vulnerability points (Max 10)
        vuln_points = min(10, (vuln_mult - 1.0) * 20) 
        score += vuln_points
        
        # 5. Farmer-reported shock (Max 5)
        if farmer_report and farmer_report.get('has_shock'):
            score += 5
            drivers.append(farmer_report.get('shock_type', 'Reported shock'))

        # Suppress escalation if confidence is too low
        if confidence < 0.8:
            score = min(score, 59)

        # Determine Band
        if score < 30:
            band = 'Green'
        elif score < 60:
            band = 'Amber'
        else:
            band = 'Red'

        return {
            'score': round(score, 1),
            'band': band,
            'confidence': round(confidence, 2),
            'drivers': drivers[:3]
        }

