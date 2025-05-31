import re
from loguru import logger
import aiofiles
from typing import AsyncGenerator, TypedDict, List
from pathlib import Path


class SectionData(TypedDict):
    number: str
    title: str
    content: List[str]
    
async def read_file(file_path: str) -> AsyncGenerator[str, None]:
    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
        async for line in f:
            yield line.strip()
            
async def parse_dpd_act(file_path: str) -> None:
    
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
    
    async for line in read_file(file_path):
        if not line:
            continue
        if chapter_regex.match(line):
            current_chapter = line.title()
            continue
        section_match = section_regex.match(line)
        
        if section_match:
            if current_section:
                logger.debug(f"Found section: {current_section['number']}")
            current_section = SectionData(
                number=f"{section_match.group(1)} {section_match.group(2)}".title(),
                title=section_match.group(3).strip().title() if section_match.group(3) else "",
                content=[]
            )
            section_content = []
            continue
        
        if current_section:
            section_content.append(line)
            
    if current_section:
        logger.debug(f'Found Section: {current_section['number']}')