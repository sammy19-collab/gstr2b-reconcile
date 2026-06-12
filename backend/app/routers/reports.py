from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user
from app.models.reconciliation import ReconciliationRun, RunStatus
from app.models.user import User
from app.services.report_excel import generate_excel_report

router = APIRouter()


@router.get("/{run_id}/excel")
def download_excel_report(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    run = db.query(ReconciliationRun).filter(ReconciliationRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run.status != RunStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Run is not yet completed")

    excel_bytes = generate_excel_report(run_id, db)

    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="reconciliation_run_{run_id}.xlsx"'
        },
    )
