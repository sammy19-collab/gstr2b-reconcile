from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, clients, uploads, reconcile, reports

app = FastAPI(
    title="GST Reconcile AI",
    description="Automated GSTR-2B reconciliation platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(clients.router, prefix="/api/v1/clients", tags=["clients"])
app.include_router(uploads.router, prefix="/api/v1/uploads", tags=["uploads"])
app.include_router(reconcile.router, prefix="/api/v1/reconcile", tags=["reconcile"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
