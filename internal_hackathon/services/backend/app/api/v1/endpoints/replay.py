import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.adapters.weather import MockWeatherAdapter
from app.adapters.market import MockMarketAdapter
from app.adapters.notification import MockNotificationAdapter
from app.scoring.engine import ScoringEngine
from app.models.farmer import FarmerProfile
from app.models.risk import RiskEvent
from app.models.case import AlertCase
from app.models.outbox import OutboxMessage

router = APIRouter()
weather_adapter = MockWeatherAdapter()
market_adapter = MockMarketAdapter()
notification_adapter = MockNotificationAdapter()
scoring_engine = ScoringEngine()

class ReplayRequest(BaseModel):
    farmer_token: str
    scenario: str = 'normal' # normal, drought, crash, drought_crash, stale

@router.post('/scenario')
def replay_scenario(request: ReplayRequest, db: Session = Depends(get_db)):
    profile = db.query(FarmerProfile).filter(FarmerProfile.farmer_token == request.farmer_token).first()
    if not profile:
        raise HTTPException(status_code=404, detail='Farmer not found')

    w_scenario = 'normal'
    m_scenario = 'normal'
    repayment = None

    if request.scenario == 'drought':
        w_scenario = 'drought'
    elif request.scenario == 'crash':
        m_scenario = 'crash'
    elif request.scenario == 'drought_crash':
        w_scenario = 'drought'
        m_scenario = 'crash'
        repayment = {'is_due_soon': True}
    elif request.scenario == 'stale':
        w_scenario = 'stale'

    weather_data = weather_adapter.get_rainfall_deviation(profile.village_id, w_scenario)
    market_data = market_adapter.get_price_deviation(profile.crop, m_scenario)

    profile_dict = {
        'irrigation_type': profile.irrigation_type,
        'crop': profile.crop
    }

    result = scoring_engine.calculate_score(profile_dict, weather_data, market_data, repayment)
    
    # Save Risk Event
    event_id = str(uuid.uuid4())
    risk_event = RiskEvent(
        event_id=event_id,
        farmer_token=profile.farmer_token,
        village_id=profile.village_id,
        score=result['score'],
        band=result['band'],
        confidence=result['confidence'],
        contributors=result['drivers'],
        action_ids=[],
        model_version='1.0'
    )
    db.add(risk_event)

    case_info = None
    if result['band'] in ['Amber', 'Red']:
        case = AlertCase(
            event_id=event_id,
            recipient_role='officer',
            channel='voice',
            sent_at=datetime.utcnow(),
            status='New'
        )
        db.add(case)
        db.commit()
        db.refresh(case)
        case_info = {'case_id': case.id, 'status': case.status}

        outbox_msg = OutboxMessage(
            message_id=str(uuid.uuid4()),
            farmer_phone=profile.phone_enc,
            channel='voice',
            content={'band': result['band'], 'drivers': result['drivers']}
        )
        db.add(outbox_msg)
        db.commit()
    else:
        db.commit()
    
    return {
        'farmer_token': profile.farmer_token,
        'scenario': request.scenario,
        'risk_event': result,
        'case': case_info
    }

