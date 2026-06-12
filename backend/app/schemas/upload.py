from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, List, Any


class UploadOut(BaseModel):
    id: int
    client_id: int
    upload_type: str
    filename: str
    file_size: int
    row_count: Optional[int] = None
    period: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class ColumnMappingCreate(BaseModel):
    mapping: Dict[str, str]  # {"canonical_field": "source_column"}


class ColumnMappingOut(BaseModel):
    id: int
    upload_id: int
    mapping: Dict[str, str]
    created_at: datetime
    model_config = {"from_attributes": True}


class MappingDetectResponse(BaseModel):
    detected: Dict[str, str]  # auto-detected canonical -> source
    unresolved: List[str]  # canonical fields not auto-mapped
    sample_columns: List[str]  # actual columns from the file
