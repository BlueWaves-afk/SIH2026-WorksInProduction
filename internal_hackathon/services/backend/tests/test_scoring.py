from app.scoring.engine import ScoringEngine

def test_legacy_shape_delegates_to_fdi_v2_engine():
    engine = ScoringEngine()
    profile = {'irrigation_type': 'rainfed', 'crop': 'cotton', 'area_band': '<1 ha'}
    weather = {'value': -28, 'ttl': 48} # Drought
    market = {'commodity': 'cotton', 'deviation_pct': -18} # Crash
    repayment = {'is_due_soon': True}

    result = engine.calculate_score(profile, weather, market, repayment)
    
    # FDI v2 uses 50/70 bands and scores -28%/-18% at their defined buckets.
    assert result['score'] == 55.9
    assert result['band'] == 'Amber'
    assert len(result['drivers']) == 3
    # Missing optional source snapshots correctly lower confidence in FDI v2.
    assert 0 < result['confidence'] < 1

def test_stale_data_suppresses_escalation():
    engine = ScoringEngine()
    profile = {'irrigation_type': 'rainfed', 'crop': 'cotton', 'area_band': '<1 ha'}
    weather = {'value': -28, 'ttl': -24} # Stale data
    market = None
    repayment = None

    result = engine.calculate_score(profile, weather, market, repayment)
    
    assert result['band'] in ['Green', 'Amber']
    assert result['score'] <= 59
    assert result['confidence'] < 1.0
