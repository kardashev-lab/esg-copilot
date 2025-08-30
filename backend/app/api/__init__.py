# API routes
from fastapi import APIRouter
from app.api.routes import chat, compliance, documents, reports

api_router = APIRouter()

# Include all route modules
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(compliance.router, prefix="/compliance", tags=["compliance"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])

# Import and include new routes
try:
    from app.api.routes import supply_chain
    api_router.include_router(supply_chain.router, prefix="/supply-chain", tags=["supply-chain"])
except ImportError:
    pass  # Route not available yet
