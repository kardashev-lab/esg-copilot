import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

class SupplyChainAnalyzer:
    """Service for analyzing supply chain risks and compliance issues"""
    
    def __init__(self):
        self.risk_keywords = {
            'child_labor': [
                'child labor', 'child labour', 'underage worker', 'minor worker',
                'child employment', 'child worker', 'young worker', 'juvenile worker'
            ],
            'forced_labor': [
                'forced labor', 'forced labour', 'involuntary work', 'coerced work',
                'human trafficking', 'modern slavery', 'bonded labor', 'debt bondage'
            ],
            'unsafe_conditions': [
                'unsafe working conditions', 'hazardous workplace', 'dangerous conditions',
                'safety violation', 'health hazard', 'unsafe environment', 'dangerous work'
            ],
            'environmental_noncompliance': [
                'environmental violation', 'pollution', 'toxic waste', 'hazardous waste',
                'environmental non-compliance', 'environmental breach', 'pollution incident'
            ],
            'wage_violations': [
                'wage violation', 'unpaid wages', 'below minimum wage', 'wage theft',
                'overtime violation', 'unpaid overtime', 'wage non-compliance'
            ],
            'discrimination': [
                'discrimination', 'harassment', 'unequal treatment', 'bias',
                'prejudice', 'exclusion', 'discriminatory practice'
            ]
        }
        
        self.compliance_standards = {
            'labor_rights': ['ILO', 'UN Guiding Principles', 'OECD Guidelines'],
            'environmental': ['ISO 14001', 'EPA standards', 'local environmental laws'],
            'safety': ['OSHA', 'ISO 45001', 'local safety regulations'],
            'human_rights': ['UN Declaration of Human Rights', 'Universal Declaration']
        }
    
    async def analyze_supplier_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze supplier documents for risks and compliance issues"""
        
        analysis_results = {
            'total_documents': len(documents),
            'risk_findings': [],
            'compliance_gaps': [],
            'risk_score': 0.0,
            'compliance_score': 0.0,
            'recommendations': [],
            'analysis_date': datetime.utcnow().isoformat()
        }
        
        total_risks = 0
        total_compliance_issues = 0
        
        for doc in documents:
            content = doc.get('content', '').lower()
            metadata = doc.get('metadata', {})
            
            # Analyze for risks
            doc_risks = self._identify_risks(content, metadata)
            analysis_results['risk_findings'].extend(doc_risks)
            total_risks += len(doc_risks)
            
            # Analyze for compliance gaps
            doc_compliance = self._identify_compliance_gaps(content, metadata)
            analysis_results['compliance_gaps'].extend(doc_compliance)
            total_compliance_issues += len(doc_compliance)
        
        # Calculate scores
        analysis_results['risk_score'] = self._calculate_risk_score(total_risks, len(documents))
        analysis_results['compliance_score'] = self._calculate_compliance_score(total_compliance_issues, len(documents))
        
        # Generate recommendations
        analysis_results['recommendations'] = self._generate_recommendations(analysis_results)
        
        return analysis_results
    
    def _identify_risks(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify specific risks in document content"""
        
        risks = []
        
        for risk_type, keywords in self.risk_keywords.items():
            for keyword in keywords:
                if keyword in content:
                    risk = {
                        'type': risk_type,
                        'keyword': keyword,
                        'severity': self._assess_risk_severity(risk_type, content),
                        'context': self._extract_context(content, keyword),
                        'source': metadata.get('filename', 'Unknown'),
                        'detected_at': datetime.utcnow().isoformat()
                    }
                    risks.append(risk)
        
        return risks
    
    def _identify_compliance_gaps(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify compliance gaps against standards"""
        
        gaps = []
        
        for standard_category, standards in self.compliance_standards.items():
            for standard in standards:
                if standard.lower() not in content.lower():
                    gap = {
                        'category': standard_category,
                        'standard': standard,
                        'gap_type': 'missing_reference',
                        'description': f'No reference to {standard} found',
                        'source': metadata.get('filename', 'Unknown'),
                        'detected_at': datetime.utcnow().isoformat()
                    }
                    gaps.append(gap)
        
        return gaps
    
    def _assess_risk_severity(self, risk_type: str, content: str) -> str:
        """Assess the severity of a detected risk"""
        
        severity_indicators = {
            'high': ['critical', 'severe', 'urgent', 'immediate', 'serious'],
            'medium': ['moderate', 'significant', 'concerning', 'important'],
            'low': ['minor', 'slight', 'potential', 'possible']
        }
        
        content_lower = content.lower()
        
        for severity, indicators in severity_indicators.items():
            for indicator in indicators:
                if indicator in content_lower:
                    return severity
        
        # Default severity based on risk type
        high_severity_types = ['child_labor', 'forced_labor', 'unsafe_conditions']
        medium_severity_types = ['environmental_noncompliance', 'wage_violations']
        
        if risk_type in high_severity_types:
            return 'high'
        elif risk_type in medium_severity_types:
            return 'medium'
        else:
            return 'low'
    
    def _extract_context(self, content: str, keyword: str) -> str:
        """Extract context around a detected keyword"""
        
        try:
            index = content.lower().find(keyword.lower())
            if index != -1:
                start = max(0, index - 100)
                end = min(len(content), index + len(keyword) + 100)
                context = content[start:end]
                return context.strip()
        except:
            pass
        
        return f"Keyword '{keyword}' detected in document"
    
    def _calculate_risk_score(self, total_risks: int, total_documents: int) -> float:
        """Calculate overall risk score (0-100, lower is better)"""
        
        if total_documents == 0:
            return 100.0
        
        # Base score starts at 100, deduct points for each risk
        base_score = 100.0
        risk_penalty = min(total_risks * 10, 100)  # Max 10 points per risk, cap at 100
        
        return max(0.0, base_score - risk_penalty)
    
    def _calculate_compliance_score(self, total_gaps: int, total_documents: int) -> float:
        """Calculate compliance score (0-100, higher is better)"""
        
        if total_documents == 0:
            return 0.0
        
        # Base score starts at 100, deduct points for each gap
        base_score = 100.0
        gap_penalty = min(total_gaps * 5, 100)  # Max 5 points per gap, cap at 100
        
        return max(0.0, base_score - gap_penalty)
    
    def _generate_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis results"""
        
        recommendations = []
        
        # Risk-based recommendations
        high_risks = [r for r in analysis_results['risk_findings'] if r['severity'] == 'high']
        if high_risks:
            recommendations.append("Immediate action required: Address high-severity risks identified in supplier documents")
        
        child_labor_risks = [r for r in analysis_results['risk_findings'] if r['type'] == 'child_labor']
        if child_labor_risks:
            recommendations.append("Conduct immediate investigation for potential child labor violations")
        
        forced_labor_risks = [r for r in analysis_results['risk_findings'] if r['type'] == 'forced_labor']
        if forced_labor_risks:
            recommendations.append("Investigate potential forced labor issues in supply chain")
        
        # Compliance-based recommendations
        if analysis_results['compliance_score'] < 80:
            recommendations.append("Improve supplier compliance documentation and training")
        
        labor_gaps = [g for g in analysis_results['compliance_gaps'] if g['category'] == 'labor_rights']
        if labor_gaps:
            recommendations.append("Enhance labor rights compliance training for suppliers")
        
        environmental_gaps = [g for g in analysis_results['compliance_gaps'] if g['category'] == 'environmental']
        if environmental_gaps:
            recommendations.append("Strengthen environmental compliance requirements for suppliers")
        
        # General recommendations
        if analysis_results['risk_score'] < 70:
            recommendations.append("Implement enhanced supplier monitoring and audit program")
        
        if len(analysis_results['risk_findings']) > 10:
            recommendations.append("Consider supplier code of conduct training and certification program")
        
        return recommendations
    
    async def analyze_supplier_performance(self, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze supplier performance metrics"""
        
        performance_analysis = {
            'supplier_id': supplier_data.get('supplier_id'),
            'risk_assessment': {},
            'compliance_status': {},
            'performance_score': 0.0,
            'recommendations': []
        }
        
        # Analyze audit results
        audit_score = self._calculate_audit_score(supplier_data)
        performance_analysis['risk_assessment']['audit_score'] = audit_score
        
        # Analyze compliance metrics
        compliance_score = self._calculate_supplier_compliance_score(supplier_data)
        performance_analysis['compliance_status']['overall_score'] = compliance_score
        
        # Calculate overall performance score
        performance_analysis['performance_score'] = (audit_score + compliance_score) / 2
        
        # Generate recommendations
        performance_analysis['recommendations'] = self._generate_supplier_recommendations(supplier_data)
        
        return performance_analysis
    
    def _calculate_audit_score(self, supplier_data: Dict[str, Any]) -> float:
        """Calculate audit score based on supplier data"""
        
        try:
            # Calculate audit score based on actual audit data
            violations = supplier_data.get('violations', 0)
            audit_frequency = supplier_data.get('audit_frequency', 1)
            audit_findings = supplier_data.get('audit_findings', [])
            
            base_score = 100.0
            violation_penalty = violations * 15
            frequency_bonus = min(audit_frequency * 5, 20)
            
            # Additional penalties for critical findings
            critical_findings = len([f for f in audit_findings if f.get('severity') == 'critical'])
            critical_penalty = critical_findings * 25
            
            return max(0.0, min(100.0, base_score - violation_penalty - critical_penalty + frequency_bonus))
            
        except Exception as e:
            logger.error(f"Error calculating audit score: {e}")
            return 50.0  # Default score
    
    def _calculate_supplier_compliance_score(self, supplier_data: Dict[str, Any]) -> float:
        """Calculate compliance score for a supplier"""
        
        try:
            # Calculate compliance score based on actual compliance data
            labor_compliance = supplier_data.get('labor_compliance', 0.0)
            environmental_compliance = supplier_data.get('environmental_compliance', 0.0)
            safety_compliance = supplier_data.get('safety_compliance', 0.0)
            
            # Weight the compliance areas
            weights = {
                'labor': 0.4,
                'environmental': 0.3,
                'safety': 0.3
            }
            
            weighted_score = (
                labor_compliance * weights['labor'] +
                environmental_compliance * weights['environmental'] +
                safety_compliance * weights['safety']
            )
            
            return round(weighted_score * 100, 2)
            
        except Exception as e:
            logger.error(f"Error calculating supplier compliance score: {e}")
            return 0.0
    
    def _generate_supplier_recommendations(self, supplier_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations for supplier improvement"""
        
        recommendations = []
        
        violations = supplier_data.get('violations', 0)
        if violations > 0:
            recommendations.append(f"Address {violations} identified compliance violations")
        
        audit_frequency = supplier_data.get('audit_frequency', 1)
        if audit_frequency < 2:
            recommendations.append("Increase audit frequency to at least twice annually")
        
        labor_compliance = supplier_data.get('labor_compliance', 0.8)
        if labor_compliance < 0.9:
            recommendations.append("Improve labor rights compliance through training and monitoring")
        
        environmental_compliance = supplier_data.get('environmental_compliance', 0.8)
        if environmental_compliance < 0.9:
            recommendations.append("Enhance environmental compliance practices")
        
        return recommendations
