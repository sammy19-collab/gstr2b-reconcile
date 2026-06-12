import logging
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="tasks.run_reconciliation", max_retries=2)
def run_reconciliation(self, run_id: int) -> dict:
    """
    Celery task to run GSTR-2B reconciliation for a given run_id.
    Sets status RUNNING, calls the engine, then sets COMPLETED or FAILED.
    """
    from app.database import SessionLocal
    from app.services.matching.engine import run_reconciliation_engine
    from app.models.reconciliation import ReconciliationRun, RunStatus

    logger.info(f"Starting reconciliation task for run_id={run_id}")
    db = SessionLocal()

    try:
        run_reconciliation_engine(run_id, db)
        logger.info(f"Reconciliation run {run_id} completed successfully")
        return {"run_id": run_id, "status": "COMPLETED"}

    except Exception as exc:
        logger.error(f"Reconciliation run {run_id} failed: {exc}", exc_info=True)
        # Attempt to mark as FAILED if not already done by engine
        try:
            run = db.query(ReconciliationRun).filter(ReconciliationRun.id == run_id).first()
            if run and run.status not in (RunStatus.FAILED, RunStatus.COMPLETED):
                run.status = RunStatus.FAILED
                run.error_message = str(exc)[:1024]
                db.commit()
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=30)

    finally:
        db.close()
