from asyncpg import Pool
from app.services.document_parser import parse_user_doc
from loguru import logger
from typing import List

async def upload_document(file_path: str, pool: Pool) -> List[int]:
    logger.info(f"Uploading document: {file_path}")
    document_ids = await parse_user_doc(file_path, pool)
    return document_ids