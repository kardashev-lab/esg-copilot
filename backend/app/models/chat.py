from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class MessageType(str, Enum):
    TEXT = "text"
    FILE_UPLOAD = "file_upload"
    REPORT_GENERATION = "report_generation"
    COMPLIANCE_CHECK = "compliance_check"

class ChatMessage(BaseModel):
    id: str
    session_id: str
    role: MessageRole
    content: str
    message_type: MessageType = MessageType.TEXT
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    references: List[str] = Field(default_factory=list)  # Document IDs referenced

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context_documents: List[str] = Field(default_factory=list)
    framework_focus: Optional[str] = None  # GRI, SASB, TCFD, etc.

class ChatResponse(BaseModel):
    message_id: str
    session_id: str
    response: str
    references: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_score: float
    processing_time: float
    suggested_actions: List[str] = Field(default_factory=list)

class ChatSession(BaseModel):
    id: str
    user_id: Optional[str] = None
    title: str
    created_at: datetime
    last_activity: datetime
    message_count: int
    tags: List[str] = Field(default_factory=list)

class ChatSessionCreate(BaseModel):
    title: str
    tags: List[str] = Field(default_factory=list)
