from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import uuid
from datetime import datetime

from app.models.document import DocumentResponse, DocumentCategory, DocumentStatus
from app.services.document_processor import DocumentProcessor
from app.services.vector_store import VectorStore

router = APIRouter()
document_processor = DocumentProcessor()
vector_store = VectorStore()

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    category: DocumentCategory = Form(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form("")
):
    """Upload and process a document"""
    
    # Validate file type
    allowed_extensions = [".pdf", ".docx", ".xlsx", ".csv", ".txt"]
    file_extension = file.filename.lower().split(".")[-1] if "." in file.filename else ""
    
    if f".{file_extension}" not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Validate file size (50MB limit)
    if file.size > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 50MB limit"
        )
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Process document
        document = await document_processor.process_document(
            file_content=file_content,
            filename=file.filename,
            category=category,
            description=description
        )
        
        # Add tags if provided
        if tags:
            document.tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # If document was processed successfully, add to vector store
        if document.status == DocumentStatus.PROCESSED:
            content = document.metadata.get("extracted_content", "")
            metadata = {
                "filename": document.filename,
                "category": document.category.value,
                "description": document.description,
                "tags": document.tags,
                "file_type": document.file_type.value,
                "created_at": document.created_at.isoformat()
            }
            
            await vector_store.add_document(
                document_id=document.id,
                content=content,
                metadata=metadata
            )
        
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            file_type=document.file_type,
            category=document.category,
            status=document.status,
            created_at=document.created_at,
            processed_at=document.processed_at,
            description=document.description,
            tags=document.tags,
            metadata=document.metadata
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )

@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    category: Optional[DocumentCategory] = None,
    status: Optional[DocumentStatus] = None,
    limit: int = 50,
    offset: int = 0
):
    """List uploaded documents with optional filtering"""
    
    # In a real implementation, this would query a database
    # For now, return a mock response
    return []

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """Get a specific document by ID"""
    
    # In a real implementation, this would query a database
    # For now, return a mock response
    raise HTTPException(status_code=404, detail="Document not found")

@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its vector embeddings"""
    
    try:
        # Delete from vector store
        success = await vector_store.delete_document(document_id)
        
        if success:
            return {"message": "Document deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting document: {str(e)}"
        )

@router.get("/{document_id}/chunks")
async def get_document_chunks(document_id: str):
    """Get all chunks for a specific document"""
    
    try:
        chunks = await vector_store.get_document_chunks(document_id)
        return {
            "document_id": document_id,
            "chunks": chunks,
            "total_chunks": len(chunks)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving document chunks: {str(e)}"
        )

@router.get("/stats/overview")
async def get_document_stats():
    """Get statistics about uploaded documents and vector store"""
    
    try:
        vector_stats = await vector_store.get_collection_stats()
        
        return {
            "vector_store": vector_stats,
            "total_documents": 0,  # Would come from database
            "processing_queue": 0,  # Would come from queue system
            "storage_used": "0 MB"  # Would calculate from actual files
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving statistics: {str(e)}"
        )
