from asyncpg import Pool
from typing import List, Dict
from loguru import logger

async def insert_dpdp_act(pool: Pool, section_number: str, section_title: str, chapter: str, 
                        content: str, is_chunk: bool, chunk_index: int | None ) -> int:
    async with pool.acquire() as conn:
        return await conn.fetchval(
            """
            INSERT INTO dpdp_act(section_number, section_title, chapter, content, is_chunk, chunk_index)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
            """,
            section_number, section_title, chapter, content, is_chunk, chunk_index
        )
        
async def insert_document(pool: Pool, filename: str, chunk_text: str) -> int:
    async with pool.acquire() as conn:
        return await conn.fetchval(
            """
            INSERT INTO documents (filename, chunk_text)
            VALUES ($1, $2)
            RETURNING id
            """,
            filename, chunk_text
        )
        
async def insert_audit( pool: Pool, document_id: int, dpdp_section: str, compliance_status: bool,
                    gaps: str, suggestions: str ) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO audits (document_id, dpdp_section, compliance_status, gaps, suggestions)
            VALUES ($1, $2, $3, $4, $5)
            """,
            document_id, dpdp_section, compliance_status, gaps, suggestions
        )
        
async def fetch_document_chunks(pool: Pool, document_id: int) -> List[Dict]:
    async with pool.acquire() as conn:
        filename = await conn.fetchval(
            "SELECT filename FROM documents WHERE id = $1",
            document_id
        )
        if not filename:
            logger.error(f"No document found for document_id: {document_id}")
            return []
        
        chunks= await conn.fetch(
            """
            SELECT id, filename, chunk_text FROM Documents WHERE filename= $1 ORDER BY id 
            """,
            filename
        )
        return [dict(chunk) for chunk in chunks]
    