from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.schemas.client import ClientCreate, ClientUpdate, ClientOut
from app.models.client import Client
from app.models.user import User
from app.core.audit import write_audit

router = APIRouter()


@router.get("/", response_model=List[ClientOut])
def list_clients(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Client).filter(Client.owner_id == current_user.id).all()


@router.post("/", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
def create_client(
    body: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client = Client(
        owner_id=current_user.id,
        name=body.name,
        gstin=body.gstin,
        pan=body.pan,
        contact_email=body.contact_email,
        contact_phone=body.contact_phone,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    write_audit(db, action="CREATE_CLIENT", user_id=current_user.id,
                resource_type="client", resource_id=client.id)
    db.commit()
    return client


@router.get("/{client_id}", response_model=ClientOut)
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client = db.query(Client).filter(
        Client.id == client_id, Client.owner_id == current_user.id
    ).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client


@router.put("/{client_id}", response_model=ClientOut)
def update_client(
    client_id: int,
    body: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client = db.query(Client).filter(
        Client.id == client_id, Client.owner_id == current_user.id
    ).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    write_audit(db, action="UPDATE_CLIENT", user_id=current_user.id,
                resource_type="client", resource_id=client.id)
    db.commit()
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client = db.query(Client).filter(
        Client.id == client_id, Client.owner_id == current_user.id
    ).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    db.delete(client)
    db.commit()
    write_audit(db, action="DELETE_CLIENT", user_id=current_user.id,
                resource_type="client", resource_id=client_id)
    db.commit()
