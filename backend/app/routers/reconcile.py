from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.schemas.reconcile import (
    ReconcileRunRequest, RunStatusResponse, ResultRow, ResultsPageResponse
)
from app.schemas.report import VendorAnalyticsOut
from app.models.reconciliation import ReconciliationRun, ReconciliationResult, RunStatus
from app.models.vendor import VendorAnalytics
from app.models.user import User
from app.workers.tasks import run_reconciliation
from app.core.audit import write_audit

router = APIRouter()


@router.post("/run", response_model=RunStatusResponse, status_code=status.HTTP_202_ACCEPTED)
def start_run(
    body: ReconcileRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    run = ReconciliationRun(
        client_id=body.client_id,
        initiated_by=current_user.id,
        period=body.period,
        pr_upload_id=body.pr_upload_id,
        g2b_upload_id=body.g2b_upload_id,
        tax_tolerance=body.tax_tolerance,
        fuzzy_threshold=body.fuzzy_threshold,
        status=RunStatus.QUEUED,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    write_audit(db, action="START_RUN", user_id=current_user.id,
                resource_type="reconciliation_run", resource_id=run.id)
    db.commit()

    # Enqueue celery task
    run_reconciliation.delay(run.id)

    return RunStatusResponse(
        id=run.id,
        status=run.status.value,
        summary=None,
        created_at=run.created_at,
    )


@router.get("/{run_id}", response_model=RunStatusResponse)
def get_run_status(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    run = db.query(ReconciliationRun).filter(ReconciliationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    summary = None
    if run.summary:
        from app.schemas.reconcile import RunSummary
        summary = RunSummary(**run.summary)

    return RunStatusResponse(
        id=run.id,
        status=run.status.value,
        summary=summary,
        created_at=run.created_at,
    )


@router.get("/{run_id}/results", response_model=ResultsPageResponse)
def get_run_results(
    run_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    category: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    run = db.query(ReconciliationRun).filter(ReconciliationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    query = db.query(ReconciliationResult).filter(ReconciliationResult.run_id == run_id)
    if category:
        query = query.filter(ReconciliationResult.category == category)

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    result_rows = []
    for item in items:
        result_rows.append(ResultRow(
            id=item.id,
            category=item.category.value,
            confidence=item.confidence,
            purchase=item.purchase_data,
            gstr2b=item.gstr2b_data,
            tax_delta=item.tax_delta,
            date_delta_days=item.date_delta_days,
        ))

    return ResultsPageResponse(total=total, page=page, page_size=page_size, items=result_rows)


@router.get("/{run_id}/vendors", response_model=List[VendorAnalyticsOut])
def get_run_vendors(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    run = db.query(ReconciliationRun).filter(ReconciliationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    vendors = db.query(VendorAnalytics).filter(VendorAnalytics.run_id == run_id).all()
    return vendors
