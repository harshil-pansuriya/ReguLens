from fastapi import FastAPI
from typing import Dict, Any, AsyncContextManager
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.connection import init_db, closed_db

import uvicorn

async def lifespan(app: FastAPI) -> AsyncContextManager:   # Manage fastapi app lifecycle
    await init_db(app)
    yield
    await closed_db(app)                

app = FastAPI(title="CompliGuard: DPDP Compliance Auditor")

setup_logging()

@app.get("/", response_model=Dict[str, str])
async def root() -> Dict[str, Any]:
    return {"message": "CompliGuard API is running"}   # API Endpoint

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True
    )