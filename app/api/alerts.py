from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])

def _resp(data: Any, message: str = "OK") -> dict:
    return {"success": True, "data": data, "message": message,
            "timestamp": datetime.utcnow().isoformat()}

@router.get("")
def list_alerts(db: Session = Depends(get_db)):
    alerts = db.query(Alert).filter(Alert.resolved == False).order_by(Alert.created_at.desc()).all()
    return _resp([AlertResponse.model_validate(a).model_dump() for a in alerts], "Alerts fetched")

@router.patch("/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert: raise HTTPException(status_code=404, detail="Alert not found")
    alert.resolved = True; db.commit(); db.refresh(alert)
    return _resp(AlertResponse.model_validate(alert).model_dump(), "Alert resolved")
