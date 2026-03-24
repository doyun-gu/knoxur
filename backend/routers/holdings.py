from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_db
from models import Holding
from schemas import HoldingCreate, HoldingUpdate, HoldingOut

router = APIRouter(prefix="/api/holdings", tags=["holdings"])


@router.get("/", response_model=List[HoldingOut])
def list_holdings(account_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Holding)
    if account_id is not None:
        query = query.filter(Holding.account_id == account_id)
    return query.all()


@router.get("/{holding_id}", response_model=HoldingOut)
def get_holding(holding_id: int, db: Session = Depends(get_db)):
    holding = db.query(Holding).filter(Holding.id == holding_id).first()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")
    return holding


@router.post("/", response_model=HoldingOut, status_code=201)
def create_holding(data: HoldingCreate, db: Session = Depends(get_db)):
    holding = Holding(**data.model_dump())
    db.add(holding)
    db.commit()
    db.refresh(holding)
    return holding


@router.patch("/{holding_id}", response_model=HoldingOut)
def update_holding(holding_id: int, data: HoldingUpdate, db: Session = Depends(get_db)):
    holding = db.query(Holding).filter(Holding.id == holding_id).first()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(holding, key, value)
    db.commit()
    db.refresh(holding)
    return holding


@router.delete("/{holding_id}", status_code=204)
def delete_holding(holding_id: int, db: Session = Depends(get_db)):
    holding = db.query(Holding).filter(Holding.id == holding_id).first()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")
    db.delete(holding)
    db.commit()
