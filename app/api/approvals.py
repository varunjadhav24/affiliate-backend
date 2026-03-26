from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.approval import Approval
from app.schemas.approval import ApprovalResponse

router = APIRouter(prefix="/approvals", tags=["approvals"])

def _resp(data: Any, message: str = "OK") -> dict:
    return {"success": True, "data": data, "message": message,
            "timestamp": datetime.utcnow().isoformat()}

@router.get("")
def list_approvals(db: Session = Depends(get_db)):
    approvals = db.query(Approval).filter(Approval.status == "pending").order_by(Approval.created_at.desc()).all()
    return _resp([ApprovalResponse.model_validate(a).model_dump() for a in approvals], "Approvals fetched")

@router.post("/{approval_id}/approve")
def approve_action(approval_id: int, db: Session = Depends(get_db)):
    a = db.query(Approval).filter(Approval.id == approval_id).first()
    if not a: raise HTTPException(status_code=404, detail="Approval not found")
    if a.status != "pending": raise HTTPException(status_code=400, detail=f"Already {a.status}")
    a.status = "approved"; db.commit(); db.refresh(a)
    return _resp(ApprovalResponse.model_validate(a).model_dump(), "Approved")

@router.post("/{approval_id}/reject")
def reject_action(approval_id: int, db: Session = Depends(get_db)):
    a = db.query(Approval).filter(Approval.id == approval_id).first()
    if not a: raise HTTPException(status_code=404, detail="Approval not found")
    if a.status != "pending": raise HTTPException(status_code=400, detail=f"Already {a.status}")
    a.status = "rejected"; db.commit(); db.refresh(a)
    return _resp(ApprovalResponse.model_validate(a).model_dump(), "Rejected")
