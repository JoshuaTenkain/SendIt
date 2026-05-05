from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.address import Address
from app.models.user import User
from app.schemas.address import AddressCreate, AddressOut, AddressUpdate

router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.get("/", response_model=list[AddressOut])
def list_addresses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Address]:
    return list(db.scalars(select(Address).where(Address.user_id == current_user.id).order_by(Address.created_at.desc())))


@router.post("/", response_model=AddressOut, status_code=201)
def create_address(
    payload: AddressCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Address:
    addr = Address(user_id=current_user.id, **payload.model_dump())
    db.add(addr)
    db.commit()
    db.refresh(addr)
    return addr


@router.patch("/{address_id}", response_model=AddressOut)
def update_address(
    address_id: uuid.UUID,
    payload: AddressUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Address:
    addr = db.get(Address, address_id)
    if not addr or addr.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Address not found")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(addr, k, v)

    db.add(addr)
    db.commit()
    db.refresh(addr)
    return addr


@router.delete("/{address_id}", status_code=204, response_model=None)
def delete_address(
    address_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    addr = db.get(Address, address_id)
    if not addr or addr.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Address not found")

    db.delete(addr)
    db.commit()
    return None
