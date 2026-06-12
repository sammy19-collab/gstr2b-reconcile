from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class ClientCreate(BaseModel):
    name: str
    gstin: str  # 15 chars
    pan: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None


class ClientUpdate(ClientCreate):
    pass


class ClientOut(ClientCreate):
    id: int
    created_at: datetime
    model_config = {"from_attributes": True}
