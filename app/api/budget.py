from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.budget_allocation import BudgetAllocation
from app.models.niche import Niche

router = APIRouter(prefix="/budget-allocations", tags=["budget"])

def _resp(data: Any, message: str = "OK") -> dict:
    return {"success": True, "data": data, "message": message,
            "timestamp": datetime.utcnow().isoformat()}

@router.get("")
def list_budget_allocations(db: Session = Depends(get_db)):
    result = []
    for alloc in db.query(BudgetAllocation).all():
        niche = db.query(Niche).filter(Niche.id == alloc.niche_id).first()
        result.append({"id": alloc.id, "niche_id": alloc.niche_id,
                       "niche_name": niche.name if niche else None,
                       "allocated": alloc.allocated, "spent": alloc.spent,
                       "remaining": round(alloc.allocated - alloc.spent, 2),
                       "utilization_pct": round((alloc.spent / alloc.allocated) * 100, 1) if alloc.allocated > 0 else 0.0,
                       "updated_at": alloc.updated_at.isoformat() if alloc.updated_at else None})
    return _resp(result, "Budget allocations fetched")
