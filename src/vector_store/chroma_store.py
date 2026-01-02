import chromadb

from typing import List, cast
from src.core.config import settings
from src.models.schemas import KnowledgeChunk
from sentence_transformers import SentenceTransformer

class BotanicalKnowledgeBase:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
        self.embedding_fn = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
        self.collection = self.client.get_or_create_collection(
            name="botanical_knowledge",
            metadata={"hnsw:space": "cosine"}
        )

    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Helper to get embeddings from local model.
        """
        embeddings = self.embedding_fn.encode(texts)
        return embeddings.tolist()
    
    def _get_query_embedding(self, text: str) -> List[float]:
        embedding = self.embedding_fn.encode(text)
        return embedding.tolist()

    def add_documents(self, documents: List[str], metadatas: List[dict], ids: List[str]):
        """
        Embeds and adds documents to the collection.
        """
        embeddings = self._get_embeddings(documents)
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

    def query(self, query_text: str, n_results: int = 3) -> List[KnowledgeChunk]:
        """
        Queries the knowledge base.
        """
        query_embedding = self._get_query_embedding(query_text)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Unpack results
        chunks = []
        if results['ids']:
            for i in range(len(results['ids'][0])):
                chunks.append(KnowledgeChunk(
                    id=results['ids'][0][i],
                    content=results['documents'][0][i],
                    source=results['metadatas'][0][i].get('source', 'unknown'),
                    metadata=results['metadatas'][0][i]
                ))
        return chunks
