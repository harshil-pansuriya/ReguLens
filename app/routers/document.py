from fastapi import APIRouter, UploadFile, Request, HTTPException
from pydantic import BaseModel
from typing import List
from app.controllers.documents import DocumentController
from app.services.embedding import EmbeddingService
from app.services.llm import LLMService
from pathlib import Path
import aiofiles

router= APIRouter(prefix='/documents', tags=['Documents'])

class UploadResponse(BaseModel):
    document_ids: List[int]
    filename: str
    
class AuditResponse(BaseModel):
    document_id: int
    filename: str
    compliance_status: bool
    dpdp_sections_analyzed: str
    compliance_gaps: str
    recommendations: str

def get_controller(request: Request) -> DocumentController:
    return DocumentController(
        embedding_service= EmbeddingService(),
        llm_service= LLMService()
    )
    
@router.post('/upload', response_model= UploadResponse)
async def upload_doc(file: UploadFile, request: Request) -> UploadResponse:
    allowed_types = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only PDF or DOCX files allowed")
    
    temp_dir=Path('temp')
    temp_dir.mkdir(exist_ok=True)
    temp_path = temp_dir / file.filename
    
    async with aiofiles.open(temp_path, 'wb') as f:
        await f.write(await file.read())
        
    controller= get_controller(request)
    document_ids = await controller.upload_document(str(temp_path), request.app.state.db_pool)
    return UploadResponse(document_ids= document_ids, filename= file.filename)

@router.post("/audit/{document_id}", response_model=AuditResponse)
async def audit_document(document_id: int, request: Request) -> AuditResponse:
    controller = get_controller(request)
    result = await controller.audit_document(document_id, request.app.state.db_pool)
    return AuditResponse(**result)