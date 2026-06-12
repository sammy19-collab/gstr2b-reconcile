import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Form
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.schemas.upload import UploadOut, ColumnMappingCreate, ColumnMappingOut, MappingDetectResponse
from app.models.upload import Upload, ColumnMapping, UploadType, UploadStatus
from app.models.user import User
from app.services.ingestion import parse_file_to_dataframe
from app.services.mapping import auto_map, PURCHASE_CANONICAL_FIELDS, GSTR2B_CANONICAL_FIELDS
from app.config import get_settings
from app.core.audit import write_audit

router = APIRouter()
settings = get_settings()


@router.post("/", response_model=UploadOut, status_code=status.HTTP_201_CREATED)
async def upload_file(
    client_id: int = Form(...),
    upload_type: str = Form(...),
    period: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate upload_type
    try:
        ut = UploadType(upload_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid upload_type: {upload_type}")

    # Check file size
    content = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")

    # Validate magic bytes
    filename_lower = file.filename.lower() if file.filename else ""
    if filename_lower.endswith(".xlsx"):
        if not content[:4] == b"PK\x03\x04":
            raise HTTPException(status_code=400, detail="Invalid XLSX file (bad magic bytes)")
    elif filename_lower.endswith(".csv"):
        try:
            content[:1024].decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Invalid CSV file (not valid UTF-8 text)")
    else:
        raise HTTPException(status_code=400, detail="Only .xlsx and .csv files are supported")

    # Save file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    unique_name = f"{uuid.uuid4()}_{file.filename}"
    filepath = os.path.join(settings.UPLOAD_DIR, unique_name)
    with open(filepath, "wb") as f:
        f.write(content)

    # Parse to count rows
    try:
        df = parse_file_to_dataframe(filepath, settings.MAX_ROWS)
        row_count = len(df)
        upload_status = UploadStatus.READY
        error_message = None
    except Exception as e:
        row_count = None
        upload_status = UploadStatus.FAILED
        error_message = str(e)

    upload = Upload(
        client_id=client_id,
        uploader_id=current_user.id,
        upload_type=ut,
        filename=file.filename,
        filepath=filepath,
        file_size=len(content),
        row_count=row_count,
        period=period,
        status=upload_status,
        error_message=error_message,
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    write_audit(db, action="UPLOAD_FILE", user_id=current_user.id,
                resource_type="upload", resource_id=upload.id)
    db.commit()
    return upload


@router.get("/{upload_id}", response_model=UploadOut)
def get_upload(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    upload = db.query(Upload).filter(Upload.id == upload_id, Upload.uploader_id == current_user.id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    return upload


@router.get("/{upload_id}/mapping", response_model=MappingDetectResponse)
def detect_mapping(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    upload = db.query(Upload).filter(Upload.id == upload_id, Upload.uploader_id == current_user.id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    df = parse_file_to_dataframe(upload.filepath, settings.MAX_ROWS)
    sample_columns = list(df.columns)

    canonical_fields = (
        PURCHASE_CANONICAL_FIELDS
        if upload.upload_type == UploadType.PURCHASE_REGISTER
        else GSTR2B_CANONICAL_FIELDS
    )

    detected, unresolved = auto_map(sample_columns, canonical_fields)
    return MappingDetectResponse(
        detected=detected,
        unresolved=unresolved,
        sample_columns=sample_columns,
    )


@router.post("/{upload_id}/mapping", response_model=ColumnMappingOut)
def save_mapping(
    upload_id: int,
    body: ColumnMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    upload = db.query(Upload).filter(Upload.id == upload_id, Upload.uploader_id == current_user.id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    existing = db.query(ColumnMapping).filter(ColumnMapping.upload_id == upload_id).first()
    if existing:
        existing.mapping = body.mapping
        db.commit()
        db.refresh(existing)
        return existing

    mapping = ColumnMapping(upload_id=upload_id, mapping=body.mapping)
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    return mapping
