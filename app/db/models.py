from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class DPDPAct(Base):
    
    __tablename__ = 'dpdp_act'
    id = Column(Integer, primary_key=True)
    section_number = Column(String(50), nullable=False)
    section_title = Column(Text)
    chapter = Column(String(100))
    content = Column(Text, nullable=False)
    is_chunk = Column(Boolean, default=False)
    chunk_index = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Document(Base):
    
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    chunk_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Audit(Base):
    
    __tablename__ = "audits"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    dpdp_section = Column(String(500))
    compliance_status = Column(Boolean)
    gaps = Column(Text)
    suggestions = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)