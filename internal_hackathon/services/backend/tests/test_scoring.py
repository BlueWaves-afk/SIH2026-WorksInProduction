from app.scoring.engine import ScoringEngine

def test_scoring_drought_and_crash():
    engine = ScoringEngine()
    profile = {'irrigation_type': 'rainfed', 'crop': 'cotton'}
    weather = {'value': -28, 'ttl': 48} # Drought
    market = {'commodity': 'cotton', 'deviation_pct': -18} # Crash
    repayment = {'is_due_soon': True}

    result = engine.calculate_score(profile, weather, market, repayment)
    
    assert result['score'] >= 60
    assert result['band'] == 'Red'
    assert len(result['drivers']) == 3
    assert result['confidence'] == 1.0

def test_stale_data_suppresses_escalation():
    engine = ScoringEngine()
    profile = {'irrigation_type': 'rainfed', 'crop': 'cotton'}
    weather = {'value': -28, 'ttl': -24} # Stale data
    market = None
    repayment = None

    result = engine.calculate_score(profile, weather, market, repayment)
    
    # Normally drought gives 35 points, but confidence < 0.8 should cap to 59
    assert result['band'] in ['Green', 'Amber']
    assert result['score'] <= 59
    assert result['confidence'] < 1.0

