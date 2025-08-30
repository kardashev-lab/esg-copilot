from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    CSV = "csv"
    TXT = "txt"

class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"

class DocumentCategory(str, Enum):
    FRAMEWORK = "framework"
    COMPANY_DATA = "company_data"
    REGULATORY = "regulatory"
    PEER_REPORT = "peer_report"
    INTERNAL = "internal"

class DocumentBase(BaseModel):
    filename: str
    file_type: DocumentType
    category: DocumentCategory
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    id: str
    file_path: str
    file_size: int
    status: DocumentStatus
    created_at: datetime
    processed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: DocumentType
    category: DocumentCategory
    status: DocumentStatus
    created_at: datetime
    processed_at: Optional[datetime] = None
    description: Optional[str] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}

class DocumentChunk(BaseModel):
    id: str
    document_id: str
    content: str
    chunk_index: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
