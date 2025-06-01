from asyncpg import Pool
from loguru import logger
from typing import List, Dict
from datetime import datetime

async def insert_dpdp_act( pool: Pool, section_number: str, section_title: str, chapter: str,
                            content: str, is_chunk: bool, chunk_index: int | None ) -> int:
    query = """
        INSERT INTO dpdp_act (section_number, section_title, chapter, content, is_chunk, chunk_index)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id
    """
    async with pool.acquire() as conn:
        section_id = await conn.fetchval(
            query, section_number, section_title, chapter, content, is_chunk, chunk_index
        )
        logger.debug(f"Inserted DPDP Act section {section_number} with ID: {section_id}")
        return section_id

async def insert_document(pool: Pool, filename: str, chunk_text: str) -> int:

    query = """
        INSERT INTO documents (filename, chunk_text)
        VALUES ($1, $2)
        RETURNING id
    """
    async with pool.acquire() as conn:
        document_id = await conn.fetchval(query, filename, chunk_text)
        logger.debug(f"Inserted document chunk for {filename} with ID: {document_id}")
        return document_id

async def insert_audit( pool: Pool, document_id: int, dpdp_section: str, compliance_status: bool,
                        gaps: str, suggestions: str ) -> None:
    query = """
        INSERT INTO audits (document_id, dpdp_section, compliance_status, gaps, suggestions)
        VALUES ($1, $2, $3, $4, $5)
    """
    async with pool.acquire() as conn:
        await conn.execute(
            query, document_id, dpdp_section, compliance_status, gaps, suggestions
        )
        logger.debug(f"Inserted audit for document_id: {document_id}")

async def fetch_document_chunks(pool: Pool, document_id: int) -> List[Dict]:
    
    query = """
            SELECT id, filename, chunk_text FROM documents WHERE id = $1
            """
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, document_id)
        if not rows:
            logger.error(f"No document found with ID: {document_id}")
            raise ValueError(f"Document ID {document_id} not found")
        return [
            { 
                "id": row["id"], 
                "filename": row["filename"], 
                "chunk_text": row["chunk_text"]
            }
            for row in rows
        ]