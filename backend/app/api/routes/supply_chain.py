from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from pydantic import BaseModel

from app.services.supply_chain_analyzer import SupplyChainAnalyzer
from app.services.vector_store import VectorStore

router = APIRouter()
supply_chain_analyzer = SupplyChainAnalyzer()
vector_store = VectorStore()

class SupplyChainAnalysisRequest(BaseModel):
    supplier_documents: List[str] = []
    analysis_type: str = "comprehensive"  # comprehensive, risk_focused, compliance_focused
    risk_threshold: float = 0.7
    include_recommendations: bool = True

class SupplierPerformanceRequest(BaseModel):
    supplier_id: str
    supplier_data: Dict[str, Any]

@router.post("/analyze")
async def analyze_supply_chain(request: SupplyChainAnalysisRequest):
    """Analyze supply chain documents for risks and compliance issues"""
    
    try:
        # Get supplier documents from vector store
        documents = []
        for doc_id in request.supplier_documents:
            chunks = await vector_store.get_document_chunks(doc_id)
            documents.extend(chunks)
        
        # Perform supply chain analysis
        analysis_results = await supply_chain_analyzer.analyze_supplier_documents(documents)
        
        # Add request metadata
        analysis_results['request_id'] = str(uuid.uuid4())
        analysis_results['analysis_type'] = request.analysis_type
        analysis_results['risk_threshold'] = request.risk_threshold
        analysis_results['total_documents_analyzed'] = len(documents)
        
        return analysis_results
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing supply chain: {str(e)}"
        )

@router.post("/supplier/performance")
async def analyze_supplier_performance(request: SupplierPerformanceRequest):
    """Analyze individual supplier performance"""
    
    try:
        # Analyze supplier performance
        performance_analysis = await supply_chain_analyzer.analyze_supplier_performance(
            request.supplier_data
        )
        
        return performance_analysis
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing supplier performance: {str(e)}"
        )

@router.post("/upload-supplier-documents")
async def upload_supplier_documents(
    files: List[UploadFile] = File(...),
    supplier_id: Optional[str] = None
):
    """Upload supplier documents for analysis"""
    
    try:
        uploaded_documents = []
        
        for file in files:
            # Validate file type
            allowed_extensions = [".pdf", ".docx", ".txt", ".csv"]
            file_extension = file.filename.lower().split(".")[-1] if "." in file.filename else ""
            
            if f".{file_extension}" not in allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"File type not supported: {file.filename}"
                )
            
            # Read file content
            file_content = await file.read()
            
            # Create document metadata
            document_metadata = {
                "filename": file.filename,
                "supplier_id": supplier_id,
                "upload_date": datetime.utcnow().isoformat(),
                "file_type": file_extension,
                "category": "supplier_document"
            }
            
            # Add to vector store
            document_id = str(uuid.uuid4())
            await vector_store.add_document(
                document_id=document_id,
                content=file_content.decode('utf-8', errors='ignore'),
                metadata=document_metadata
            )
            
            uploaded_documents.append({
                "document_id": document_id,
                "filename": file.filename,
                "supplier_id": supplier_id,
                "status": "uploaded"
            })
        
        return {
            "message": f"Successfully uploaded {len(uploaded_documents)} documents",
            "uploaded_documents": uploaded_documents
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading supplier documents: {str(e)}"
        )

@router.get("/risks/summary")
async def get_supply_chain_risk_summary():
    """Get summary of supply chain risks"""
    
    try:
        # Mock risk summary - in real implementation, this would query actual data
        risk_summary = {
            "total_suppliers": 1500,
            "suppliers_analyzed": 1200,
            "high_risk_suppliers": 45,
            "medium_risk_suppliers": 120,
            "low_risk_suppliers": 1035,
            "risk_distribution": {
                "child_labor": 5,
                "forced_labor": 8,
                "unsafe_conditions": 25,
                "environmental_noncompliance": 15,
                "wage_violations": 12,
                "discrimination": 8
            },
            "compliance_score": 87.5,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return risk_summary
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting risk summary: {str(e)}"
        )

@router.get("/suppliers/{supplier_id}/analysis")
async def get_supplier_analysis(supplier_id: str):
    """Get analysis results for a specific supplier"""
    
    try:
        # Mock supplier analysis - in real implementation, this would query actual data
        supplier_analysis = {
            "supplier_id": supplier_id,
            "supplier_name": f"Supplier {supplier_id}",
            "risk_assessment": {
                "overall_risk_score": 0.35,
                "risk_level": "medium",
                "risk_factors": [
                    "Environmental compliance issues",
                    "Safety training gaps"
                ]
            },
            "compliance_status": {
                "overall_score": 82.0,
                "labor_compliance": 85.0,
                "environmental_compliance": 78.0,
                "safety_compliance": 83.0
            },
            "audit_history": [
                {
                    "audit_date": "2023-06-15",
                    "audit_type": "Comprehensive",
                    "score": 85.0,
                    "findings": 3,
                    "status": "Passed"
                },
                {
                    "audit_date": "2022-12-10",
                    "audit_type": "Focused",
                    "score": 78.0,
                    "findings": 5,
                    "status": "Passed with conditions"
                }
            ],
            "recommendations": [
                "Implement enhanced environmental management system",
                "Increase safety training frequency",
                "Develop corrective action plan for identified issues"
            ],
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return supplier_analysis
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting supplier analysis: {str(e)}"
        )

@router.get("/dashboard/metrics")
async def get_supply_chain_dashboard_metrics():
    """Get metrics for supply chain dashboard"""
    
    try:
        # Mock dashboard metrics - in real implementation, this would query actual data
        dashboard_metrics = {
            "overview": {
                "total_suppliers": 1500,
                "active_suppliers": 1420,
                "suspended_suppliers": 80,
                "compliance_rate": 87.5
            },
            "risk_metrics": {
                "high_risk_suppliers": 45,
                "medium_risk_suppliers": 120,
                "low_risk_suppliers": 1035,
                "risk_trend": "decreasing"
            },
            "compliance_metrics": {
                "fully_compliant": 1200,
                "partially_compliant": 200,
                "non_compliant": 100,
                "compliance_trend": "improving"
            },
            "audit_metrics": {
                "audits_this_year": 450,
                "audits_scheduled": 180,
                "average_audit_score": 84.2,
                "audit_completion_rate": 92.0
            },
            "performance_metrics": {
                "on_time_delivery": 94.5,
                "quality_score": 96.2,
                "cost_variance": -2.1,
                "supplier_satisfaction": 8.7
            }
        }
        
        return dashboard_metrics
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting dashboard metrics: {str(e)}"
        )

@router.get("/reports/risk-assessment")
async def generate_risk_assessment_report(
    supplier_ids: Optional[List[str]] = None,
    risk_level: Optional[str] = None,
    format: str = "json"
):
    """Generate supply chain risk assessment report"""
    
    try:
        # Mock risk assessment report - in real implementation, this would generate actual report
        risk_report = {
            "report_id": str(uuid.uuid4()),
            "report_date": datetime.utcnow().isoformat(),
            "scope": {
                "supplier_ids": supplier_ids or ["all"],
                "risk_level": risk_level or "all",
                "total_suppliers_analyzed": 1200
            },
            "executive_summary": {
                "overall_risk_level": "medium",
                "key_findings": [
                    "15 suppliers identified as high risk",
                    "Environmental compliance is the most common issue",
                    "85% of suppliers meet basic compliance requirements"
                ],
                "recommendations": [
                    "Implement enhanced monitoring for high-risk suppliers",
                    "Develop targeted training programs for common compliance issues",
                    "Establish regular risk assessment review process"
                ]
            },
            "detailed_findings": {
                "high_risk_suppliers": [
                    {
                        "supplier_id": "SUP001",
                        "supplier_name": "Supplier A",
                        "risk_score": 0.85,
                        "primary_risks": ["environmental_noncompliance", "safety_violations"],
                        "recommended_actions": ["Immediate audit", "Corrective action plan"]
                    }
                ],
                "risk_distribution": {
                    "child_labor": 5,
                    "forced_labor": 8,
                    "unsafe_conditions": 25,
                    "environmental_noncompliance": 15,
                    "wage_violations": 12,
                    "discrimination": 8
                }
            },
            "compliance_analysis": {
                "overall_compliance_rate": 87.5,
                "compliance_by_category": {
                    "labor_rights": 92.0,
                    "environmental": 85.0,
                    "safety": 88.0,
                    "business_ethics": 91.0
                }
            },
            "action_plan": {
                "immediate_actions": [
                    "Conduct audits for all high-risk suppliers within 30 days",
                    "Develop corrective action plans for identified issues"
                ],
                "short_term_actions": [
                    "Implement enhanced monitoring system",
                    "Provide training for common compliance issues"
                ],
                "long_term_actions": [
                    "Establish supplier development program",
                    "Integrate risk assessment into procurement process"
                ]
            }
        }
        
        return risk_report
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating risk assessment report: {str(e)}"
        )
