import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import uuid
import json

from app.core.config import settings

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="esg_documents",
            metadata={"description": "ESG documents and framework knowledge base"}
        )
    
    async def add_document(self, document_id: str, content: str, metadata: Dict[str, Any]) -> List[str]:
        """Add document content to vector store"""
        
        # Split content into chunks
        chunks = self._chunk_content(content)
        chunk_ids = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_chunk_{i}"
            chunk_ids.append(chunk_id)
            
            # Add chunk to vector store
            self.collection.add(
                documents=[chunk],
                metadatas=[{
                    **metadata,
                    "document_id": document_id,
                    "chunk_index": i,
                    "chunk_id": chunk_id
                }],
                ids=[chunk_id]
            )
        
        return chunk_ids
    
    async def search(self, query: str, n_results: int = 5, 
                    filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filters
        )
        
        # Format results
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    'content': doc,
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if results['distances'] else None,
                    'id': results['ids'][0][i]
                })
        
        return formatted_results
    
    async def search_by_category(self, query: str, category: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search within a specific document category"""
        return await self.search(query, n_results, {"category": category})
    
    async def search_by_framework(self, query: str, framework: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Search within a specific ESG framework"""
        return await self.search(query, n_results, {"framework": framework})
    
    async def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a specific document"""
        results = self.collection.get(
            where={"document_id": document_id}
        )
        
        chunks = []
        if results['documents']:
            for i, doc in enumerate(results['documents']):
                chunks.append({
                    'content': doc,
                    'metadata': results['metadatas'][i],
                    'id': results['ids'][i]
                })
        
        # Sort by chunk index
        chunks.sort(key=lambda x: x['metadata'].get('chunk_index', 0))
        return chunks
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete all chunks for a specific document"""
        try:
            self.collection.delete(where={"document_id": document_id})
            return True
        except Exception as e:
            print(f"Error deleting document {document_id}: {e}")
            return False
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        count = self.collection.count()
        
        # Get sample documents to analyze categories
        sample_results = self.collection.get(limit=1000)
        categories = {}
        frameworks = {}
        
        if sample_results['metadatas']:
            for metadata in sample_results['metadatas']:
                category = metadata.get('category', 'unknown')
                categories[category] = categories.get(category, 0) + 1
                
                framework = metadata.get('framework', 'unknown')
                frameworks[framework] = frameworks.get(framework, 0) + 1
        
        return {
            'total_chunks': count,
            'categories': categories,
            'frameworks': frameworks
        }
    
    def _chunk_content(self, content: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split content into overlapping chunks"""
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + chunk_size
            chunk = content[start:end]
            
            # Try to break at sentence boundary
            if end < len(content):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > start + chunk_size // 2:
                    chunk = content[start:start + break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
            
            if start >= len(content):
                break
        
        return chunks
