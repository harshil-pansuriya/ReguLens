from asyncpg import Pool
from app.usecase.document import upload_document
from app.usecase.compliance import build_compliance_graph
from app.services.embedding import EmbeddingService
from app.services.llm import LLMService
from app.repository.document import fetch_document_chunks
from loguru import logger
from typing import List, Dict

class DocumentController:
    def __init__(self, embedding_service: EmbeddingService, llm_service: LLMService):
        self.embedding_service = embedding_service
        self.llm_service = llm_service
        self.compliance_graph = build_compliance_graph()

    async def upload_document(self, file_path: str, pool: Pool) -> List[int]:  # document upload
        logger.info(f"Processing upload for {file_path}")
        document_ids = await upload_document(file_path, pool)
        return document_ids

    async def audit_document(self, document_id: int, pool: Pool) -> Dict:   #audit document 
        logger.info(f"Auditing document_id: {document_id}")
        result = await self.compliance_graph.ainvoke(
            {
                "document_id": document_id,
                "document_text": "",
                "matched_sections": [],
                "audit_result": {},
                "pool": pool
            }
        )
        audit_result = result["audit_result"]
        chunks = await fetch_document_chunks(pool, document_id)
        return {
            "document_id": audit_result["document_id"],
            "filename": chunks[0]["filename"],
            "compliance_status": audit_result["compliance_status"],
            "dpdp_sections_analyzed": audit_result["dpdp_section"],
            "compliance_gaps": audit_result["gaps"],
            "recommendations": audit_result["suggestions"]
        }