from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, Index
from app.core.config import settings
from loguru import logger
from typing import List, Dict

class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index_name = "compliguard-index"
        self.index: Index | None = None
        logger.info("EmbeddingService initialized")
        
    def _get_index(self) -> Index:
        if not self.index:
            self.index= self.pc.Index(self.index_name)
            return self.index
        
    async def generate_embeddings(self, texts: List[str] ) -> List[List[float]]:
        embeddings= self.model.encode(texts, convert_to_tensor=False).tolist()
        logger.debug(f"Generated embeddings for {len(texts)} texts")
        return embeddings
    
    async def store_embeddings(self, texts: List[str], metadata:List[Dict], namespace: str) -> None:
        embeddings= await self.generate_embeddings(texts)
        
        vectors=[
            {'id': str(meta['id']), 'values': embedding, 'metadata':meta} for embedding, meta in zip(embeddings, metadata)
        ]
        
        self._get_index().upsert(vectors=vectors, namespace=namespace)  
        logger.info(f"Stored {len(vectors)} embeddings in {namespace}")
        
embedding_service= EmbeddingService()