from asyncpg import Pool
from app.services.document_parser import parse_user_doc
from app.services.embedding import EmbeddingService
from loguru import logger
from typing import List

async def upload_document(file_path: str, pool: Pool, embedding_service: EmbeddingService) -> List[int]:
    logger.info(f"Uploading document: {file_path}")
    document_ids = await parse_user_doc(file_path, pool, embedding_service)
    return document_ids