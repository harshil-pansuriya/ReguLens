from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict
from asyncpg import Pool
from pinecone import Pinecone, ServerlessSpec
from app.service.embedding import EmbeddingService
from app.service.llm import LLMService
from app.repository.document import fetch_document_chunks, insert_audit
from app.core.config import settings
from loguru import logger
from langchain.text_splitter import RecursiveCharacterTextSplitter

class ComplianceState(TypedDict):
    document_id: int
    document_text: str
    matched_sections: List[Dict]
    audit_result: Dict
    pool: Pool

async def retrieve_node(state: ComplianceState) -> ComplianceState:
    """Retrieve document text and matching DPDP Act sections."""
    pc = Pinecone(api_key=settings.pinecone_api_key)
    index_name = "compliguard-index"
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-west-2")
        )
        logger.info(f"Created Pinecone index: {index_name}")

    chunks = await fetch_document_chunks(state["pool"], state["document_id"])
    if not chunks:
        raise ValueError(f"No chunks for document_id: {state['document_id']}")

    full_text = "\n".join(chunk["chunk_text"] for chunk in chunks)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=500)
    state["document_text"] = "\n".join(text_splitter.split_text(full_text)[:2])

    embeddings = await EmbeddingService.generate_embeddings([state["document_text"]])
    index = pc.Index(index_name)
    query_result = index.query(
        vector=embeddings[0],
        top_k=10,
        include_metadata=True,
        namespace="dpdp_act"
    )

    state["matched_sections"] = [
        {
            "section_number": match["metadata"]["section_number"],
            "content": match["metadata"].get("content", ""),
            "score": match["score"]
        }
        for match in query_result["matches"]
        if not match["metadata"]["section_number"].startswith("Chunk_") and
        "content" in match["metadata"] and
        match["score"] > 0.75
    ]
    logger.info(f"Retrieved {len(state['matched_sections'])} DPDP Act sections for document_id: {state['document_id']}")
    return state

async def analyze_node(state: ComplianceState) -> ComplianceState:
    """Analyze document compliance with DPDP Act."""
    regulation_text = "\n".join(
        f"{match['section_number']}: {match['content']}" for match in state["matched_sections"]
    ) or "No relevant sections found"

    result = await LLMService.analyze_compliance(
        document_text=state["document_text"],
        regulation_text=regulation_text
    )
    dpdp_section = ", ".join(m["section_number"] for m in state["matched_sections"]) or "None"
    if len(dpdp_section) > 500:
        dpdp_section = dpdp_section[:497] + "..."

    state["audit_result"] = {
        "document_id": state["document_id"],
        "dpdp_section": dpdp_section,
        "compliance_status": result["compliance_status"],
        "gaps": result["gaps"],
        "suggestions": result["suggestions"]
    }
    return state

async def store_node(state: ComplianceState) -> ComplianceState:
    """Store audit result in database."""
    result = state["audit_result"]
    await insert_audit(
        pool=state["pool"],
        document_id=result["document_id"],
        dpdp_section=result["dpdp_section"],
        compliance_status=result["compliance_status"],
        gaps=result["gaps"],
        suggestions=result["suggestions"]
    )
    logger.info(f"Stored audit for document_id: {state['document_id']}")
    return state

def build_compliance_graph():
    """Build LangGraph compliance workflow."""
    graph = StateGraph(ComplianceState)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("analyze", analyze_node)
    graph.add_node("store", store_node)
    graph.add_edge("retrieve", "analyze")
    graph.add_edge("analyze", "store")
    graph.add_edge("store", END)
    graph.set_entry_point("retrieve")
    return graph.compile()

compliance_graph = build_compliance_graph()