from fastapi import FastAPI
from typing import Dict, Any
from app.core.config import settings
from app.core.logging import setup_logging
import uvicorn

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