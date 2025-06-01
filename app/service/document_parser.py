import re
import fitz
from docx import Document
from pathlib import Path
import aiofiles
import asyncio
from asyncpg import Pool
from loguru import logger
from typing import AsyncGenerator, TypedDict, List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.db.crud import insert_dpdp_act, insert_document
from app.core.config import settings
from app.service.embedding import embedding_service
class SectionData(TypedDict):
    number: str
    title: str
    content: List[str]
    
async def read_file(file_path: str) -> AsyncGenerator[str, None]:       # Stream lines from file
    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
        async for line in f:
            yield line.strip()
            
async def validate_section(section: SectionData) -> bool:       #validate section data 
    return bool(section['number'] and section['content'])
            
async def parse_dpd_act(file_path: str, pool: Pool) -> None:
    
    if not Path(file_path).exists():
        logger.error(f'DPDP Act file not found {file_path}')
        raise FileNotFoundError(f'file not found : {file_path}')
    
    logger.info(f"Parsing DPDP Act: {file_path}")
    chapter_regex= re.compile(r'CHAPTER\s+[IVXLC]+(?:\s+[A-Z\s]+)?', re.IGNORECASE)
    section_regex = re.compile(
        r'^(Section|Schedule)\s+(\d+\.\d*|[a-z]+\)|[A-Z]+|[IVXLC]+|[0-9]+(?:\([a-zA-Z0-9]+\))*)(?:\.)?\s*(.*)?$',
        re.IGNORECASE
    )
    
    current_chapter = "Unknown"
    current_section: SectionData | None = None
    section_content: List[str] = []
    batch_vectors: List[Dict] = []
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size ,
        chunk_overlap=settings.chunk_overlap
    )
    
    async for line in read_file(file_path):
        if not line:
            continue
        if chapter_regex.match(line):
            current_chapter = line.title()
            continue
        
        section_match = section_regex.match(line)
        if section_match:
            if current_section and validate_section(current_section):
                await store_section(
                    pool, current_chapter,current_section, section_content, text_splitter, batch_vectors
                )
                
            current_section = SectionData(
                number=f"{section_match.group(1)} {section_match.group(2)}".title(),
                title=section_match.group(3).strip().title() if section_match.group(3) else "",
                content=[]
            )
            section_content = []
            continue
        
        if current_section:
            section_content.append(line)
            
    if current_section and validate_section(current_section):
        await store_section(
            pool, current_chapter, current_section, section_content, text_splitter, batch_vectors
        )
        
    if batch_vectors:
        await asyncio.gather(
            *[
                embedding_service.store_embeddings(
                    texts=[item["text"]],
                    metadata=[item["metadata"]],
                    namespace="dpdp_act"
                )
                for item in batch_vectors
            ]
        )
        logger.info(f"Stored {len(batch_vectors)} embeddings for DPDP Act")
    
    logger.info('Completed DPDP Act parsing and storage')
        
async def store_section(pool: Pool, chapter: str, section: SectionData, content_lines: List[str], 
                        splitter: RecursiveCharacterTextSplitter, batch_vectors: List[Dict]) -> None:
    content = "\n".join(content_lines).strip()
    if not content:
        return
    
    section_id= await insert_dpdp_act( pool=pool, section_number=section["number"],
                                    section_title=section["title"], chapter=chapter, content=content,
                                    is_chunk=False, chunk_index=None )
    
    logger.debug(f"Stored section {section['number']} with ID: {section_id}")
    
    chunks= splitter.splitext(content)
    for idx, chunk in enumerate (chunks, 1):
        if not chunk.strip():
            continue
        chunk_id= await insert_dpdp_act( pool=pool, section_number=section["number"], 
                                        section_title=section["title"],chapter=chapter, content=chunk, 
                                        is_chunk=True, chunk_index=idx )
        batch_vectors.append({
            "text" : chunk,
            "metadata" : {
                "id" : chunk_id,
                "section_number": section['number'],
                "chapter": chapter,
                "chunk_index": idx,
                "content": chunk[:500],
                "type": "dpdp_act"
            }
        })
        
        logger.debug(f"Stored chunk {idx} for section {section['number']} with ID: {chunk_id}") 
        
        
        
async def parse_user_doc(file_path: str, pool: Pool) -> List[int]:
    file = Path(file_path)
    if not file.exists():
        raise FileNotFoundError(f"Document not found: {file_path}")

    logger.info(f"Parsing document: {file.name}")
    text = ""
    if file.suffix == '.pdf':
        with fitz.open(file) as doc:
            for page in doc:
                text += page.get_text()
    elif file.suffix == '.docx':
        doc = Document(file)
        text = "\n".join(para.text for para in doc.paragraphs)
    else:
        raise ValueError("Only PDF or DOCX supported")

    if not text.strip():
        raise ValueError(f"Document is empty: {file.name}")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size or 1000,
        chunk_overlap=settings.chunk_overlap or 200
    )
    chunks = text_splitter.split_text(text)
    document_ids = []
    batch_vectors = []

    for idx, chunk in enumerate(chunks, 1):
        if not chunk.strip():
            continue
        document_id = await insert_document(pool, file.name, chunk)
        document_ids.append(document_id)
        batch_vectors.append({
            "text": chunk,
            "metadata": {
                "id": document_id,
                "filename": file.name,
                "chunk_index": idx,
                "type": "document"
            }
        })

    if batch_vectors:
        await embedding_service.store_embeddings(
            texts=[item["text"] for item in batch_vectors],
            metadata=[item["metadata"] for item in batch_vectors],
            namespace="documents"
        )

    logger.info(f"Stored {len(document_ids)} chunks for {file.name}")
    return document_ids