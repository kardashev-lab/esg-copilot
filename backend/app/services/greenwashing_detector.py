import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

class GreenwashingDetector:
    """Service for detecting potential greenwashing in marketing materials and reports"""
    
    def __init__(self):
        self.vague_terms = [
            'eco-friendly', 'environmentally friendly', 'green', 'sustainable',
            'natural', 'organic', 'clean', 'pure', 'green technology',
            'environmentally conscious', 'planet-friendly', 'earth-friendly'
        ]
        
        self.unsubstantiated_claims = [
            '100% sustainable', 'completely green', 'totally eco-friendly',
            'zero impact', 'carbon neutral', 'climate positive',
            'environmentally perfect', 'completely natural'
        ]
        
        self.misleading_comparisons = [
            'better than competitors', 'industry leading', 'best in class',
            'most sustainable', 'greenest option', 'environmental leader'
        ]
        
        self.hidden_tradeoffs = [
            'while maintaining performance', 'without compromising quality',
            'with no additional cost', 'at competitive prices',
            'without sacrificing efficiency'
        ]
        
        # Common legitimate certifications for reference
        self.legitimate_certifications = [
            'iso 14001', 'leed', 'breeam', 'fsc', 'fair trade', 'b corp',
            'carbon trust', 'energy star', 'usda organic', 'eu ecolabel'
        ]
        
        # Potentially problematic certification-like terms
        self.suspicious_certifications = [
            'certified green', 'eco-certified', 'sustainability certified',
            'environmentally approved', 'green verified', 'eco-friendly certified'
        ]
        
        self.irrelevant_claims = [
            'CFC-free', 'ozone-friendly', 'biodegradable',
            'recyclable', 'renewable', 'organic'
        ]
        
        self.risk_indicators = {
            'vague_language': {
                'keywords': self.vague_terms,
                'weight': 0.3,
                'description': 'Vague or undefined environmental terms'
            },
            'unsubstantiated_claims': {
                'keywords': self.unsubstantiated_claims,
                'weight': 0.4,
                'description': 'Claims without supporting evidence'
            },
            'misleading_comparisons': {
                'keywords': self.misleading_comparisons,
                'weight': 0.2,
                'description': 'Unsupported comparative claims'
            },
            'hidden_tradeoffs': {
                'keywords': self.hidden_tradeoffs,
                'weight': 0.3,
                'description': 'Claims that hide environmental tradeoffs'
            },
            'suspicious_certifications': {
                'keywords': self.suspicious_certifications,
                'weight': 0.5,
                'description': 'Potentially unverified or suspicious environmental certifications'
            },
            'irrelevant_claims': {
                'keywords': self.irrelevant_claims,
                'weight': 0.2,
                'description': 'Claims that are legally required or irrelevant'
            }
        }
    
    async def analyze_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze documents for potential greenwashing"""
        
        analysis_results = {
            'total_documents': len(documents),
            'greenwashing_indicators': [],
            'risk_score': 0.0,
            'severity_level': 'low',
            'recommendations': [],
            'analysis_date': datetime.utcnow().isoformat()
        }
        
        total_indicators = 0
        weighted_score = 0.0
        
        for doc in documents:
            content = doc.get('content', '')
            metadata = doc.get('metadata', {})
            
            # Analyze document for greenwashing indicators
            doc_indicators = self._identify_greenwashing_indicators(content, metadata)
            analysis_results['greenwashing_indicators'].extend(doc_indicators)
            
            # Calculate weighted score
            for indicator in doc_indicators:
                indicator_type = indicator['type']
                if indicator_type in self.risk_indicators:
                    weight = self.risk_indicators[indicator_type]['weight']
                    weighted_score += weight
                    total_indicators += 1
        
        # Calculate overall risk score
        if total_indicators > 0:
            analysis_results['risk_score'] = min(100.0, (weighted_score / total_indicators) * 100)
        else:
            analysis_results['risk_score'] = 0.0
        
        # Determine severity level
        analysis_results['severity_level'] = self._determine_severity_level(analysis_results['risk_score'])
        
        # Generate recommendations
        analysis_results['recommendations'] = self._generate_recommendations(analysis_results)
        
        return analysis_results
    
    def _identify_greenwashing_indicators(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify specific greenwashing indicators in content"""
        
        indicators = []
        content_lower = content.lower()
        
        for indicator_type, config in self.risk_indicators.items():
            keywords = config['keywords']
            
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    indicator = {
                        'type': indicator_type,
                        'keyword': keyword,
                        'description': config['description'],
                        'weight': config['weight'],
                        'context': self._extract_context(content, keyword),
                        'source': metadata.get('filename', 'Unknown'),
                        'detected_at': datetime.utcnow().isoformat()
                    }
                    indicators.append(indicator)
        
        return indicators
    
    def _extract_context(self, content: str, keyword: str) -> str:
        """Extract context around a detected keyword"""
        
        try:
            index = content.lower().find(keyword.lower())
            if index != -1:
                start = max(0, index - 150)
                end = min(len(content), index + len(keyword) + 150)
                context = content[start:end]
                return context.strip()
        except:
            pass
        
        return f"Keyword '{keyword}' detected in document"
    
    def _determine_severity_level(self, risk_score: float) -> str:
        """Determine severity level based on risk score"""
        
        if risk_score >= 70:
            return 'high'
        elif risk_score >= 40:
            return 'medium'
        else:
            return 'low'
    
    def _generate_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis results"""
        
        recommendations = []
        
        # High severity recommendations
        if analysis_results['severity_level'] == 'high':
            recommendations.append("Immediate action required: Review and revise all marketing materials for accuracy")
            recommendations.append("Conduct comprehensive audit of environmental claims and supporting evidence")
            recommendations.append("Implement strict review process for all environmental marketing materials")
        
        # Medium severity recommendations
        elif analysis_results['severity_level'] == 'medium':
            recommendations.append("Review marketing materials for accuracy and substantiation of claims")
            recommendations.append("Develop clear guidelines for environmental marketing language")
            recommendations.append("Train marketing team on FTC Green Guides and environmental marketing best practices")
        
        # Specific recommendations based on indicator types
        indicator_types = [i['type'] for i in analysis_results['greenwashing_indicators']]
        
        if 'vague_language' in indicator_types:
            recommendations.append("Replace vague terms with specific, measurable environmental benefits")
        
        if 'unsubstantiated_claims' in indicator_types:
            recommendations.append("Ensure all environmental claims are supported by credible evidence and data")
        
        if 'misleading_comparisons' in indicator_types:
            recommendations.append("Remove unsupported comparative claims or provide credible benchmarking data")
        
        if 'suspicious_certifications' in indicator_types:
            recommendations.append("Verify all environmental certifications and remove unverified claims")
        
        if 'irrelevant_claims' in indicator_types:
            recommendations.append("Remove claims about legally required features or irrelevant environmental attributes")
        
        # General recommendations
        recommendations.append("Follow FTC Green Guides and other relevant environmental marketing guidelines")
        recommendations.append("Implement third-party verification for significant environmental claims")
        recommendations.append("Regularly review and update environmental marketing materials")
        
        return recommendations
    
    async def analyze_marketing_materials(self, materials: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Specifically analyze marketing materials for greenwashing"""
        
        marketing_analysis = {
            'total_materials': len(materials),
            'greenwashing_risks': [],
            'compliance_issues': [],
            'risk_score': 0.0,
            'recommendations': []
        }
        
        for material in materials:
            content = material.get('content', '')
            material_type = material.get('type', 'unknown')
            
            # Analyze for greenwashing indicators
            indicators = self._identify_greenwashing_indicators(content, material)
            
            # Check for compliance issues
            compliance_issues = self._check_marketing_compliance(content, material_type)
            
            marketing_analysis['greenwashing_risks'].extend(indicators)
            marketing_analysis['compliance_issues'].extend(compliance_issues)
        
        # Calculate risk score
        total_risks = len(marketing_analysis['greenwashing_risks'])
        total_issues = len(marketing_analysis['compliance_issues'])
        
        marketing_analysis['risk_score'] = min(100.0, (total_risks * 10) + (total_issues * 5))
        
        # Generate recommendations
        marketing_analysis['recommendations'] = self._generate_marketing_recommendations(marketing_analysis)
        
        return marketing_analysis
    
    def _check_marketing_compliance(self, content: str, material_type: str) -> List[Dict[str, Any]]:
        """Check marketing materials for compliance issues"""
        
        compliance_issues = []
        
        # Check for required disclaimers
        if 'carbon neutral' in content.lower() and 'offset' not in content.lower():
            compliance_issues.append({
                'type': 'missing_disclaimer',
                'issue': 'Carbon neutral claims without offset disclosure',
                'severity': 'high',
                'recommendation': 'Include clear disclosure about carbon offset programs'
            })
        
        # Check for specific vs general claims
        if '100%' in content.lower() and 'recycled' in content.lower():
            if 'packaging' not in content.lower() and 'materials' not in content.lower():
                compliance_issues.append({
                    'type': 'overly_broad_claim',
                    'issue': 'Broad 100% recycled claim without specificity',
                    'severity': 'medium',
                    'recommendation': 'Specify which components are 100% recycled'
                })
        
        # Check for comparative claims
        if any(word in content.lower() for word in ['best', 'most', 'leading', 'top']):
            if 'data' not in content.lower() and 'study' not in content.lower():
                compliance_issues.append({
                    'type': 'unsupported_comparison',
                    'issue': 'Comparative claim without supporting data',
                    'severity': 'medium',
                    'recommendation': 'Provide credible data to support comparative claims'
                })
        
        return compliance_issues
    
    def _generate_marketing_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate specific recommendations for marketing materials"""
        
        recommendations = []
        
        # High risk recommendations
        if analysis['risk_score'] > 70:
            recommendations.append("Immediate review required: High risk of greenwashing detected")
            recommendations.append("Consider legal review of all environmental marketing claims")
            recommendations.append("Implement mandatory approval process for environmental claims")
        
        # Specific issue recommendations
        for issue in analysis['compliance_issues']:
            recommendations.append(issue['recommendation'])
        
        # General marketing recommendations
        recommendations.append("Follow FTC Green Guides for all environmental marketing")
        recommendations.append("Use specific, measurable environmental benefits")
        recommendations.append("Provide clear, accessible supporting evidence for claims")
        recommendations.append("Avoid vague or undefined environmental terms")
        recommendations.append("Regularly audit marketing materials for accuracy")
        
        return recommendations
    
    async def validate_environmental_claims(self, claims: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate specific environmental claims against evidence"""
        
        validation_results = {
            'total_claims': len(claims),
            'validated_claims': [],
            'unvalidated_claims': [],
            'invalid_claims': [],
            'validation_score': 0.0
        }
        
        for claim in claims:
            claim_text = claim.get('claim', '')
            evidence = claim.get('evidence', [])
            
            # Validate claim against evidence
            validation = self._validate_single_claim(claim_text, evidence)
            
            if validation['is_valid']:
                validation_results['validated_claims'].append(validation)
            elif validation['has_evidence']:
                validation_results['unvalidated_claims'].append(validation)
            else:
                validation_results['invalid_claims'].append(validation)
        
        # Calculate validation score
        total_claims = len(claims)
        if total_claims > 0:
            validated_count = len(validation_results['validated_claims'])
            validation_results['validation_score'] = (validated_count / total_claims) * 100
        
        return validation_results
    
    def _validate_single_claim(self, claim: str, evidence: List[str]) -> Dict[str, Any]:
        """Validate a single environmental claim against provided evidence"""
        
        validation = {
            'claim': claim,
            'evidence': evidence,
            'is_valid': False,
            'has_evidence': len(evidence) > 0,
            'validation_notes': [],
            'recommendations': []
        }
        
        # Check if claim has supporting evidence
        if not evidence:
            validation['validation_notes'].append("No supporting evidence provided")
            validation['recommendations'].append("Provide credible evidence to support this claim")
            return validation
        
        # Check evidence quality
        evidence_quality = self._assess_evidence_quality(evidence)
        validation['evidence_quality'] = evidence_quality
        
        if evidence_quality['score'] >= 0.7:
            validation['is_valid'] = True
            validation['validation_notes'].append("Claim appears to be substantiated")
        else:
            validation['validation_notes'].append("Evidence quality is insufficient")
            validation['recommendations'].append("Provide higher quality evidence or revise claim")
        
        return validation
    
    def _assess_evidence_quality(self, evidence: List[str]) -> Dict[str, Any]:
        """Assess the quality of evidence provided for a claim"""
        
        quality_score = 0.0
        quality_indicators = []
        
        for ev in evidence:
            ev_lower = ev.lower()
            
            # Check for credible sources
            if any(source in ev_lower for source in ['study', 'research', 'report', 'data', 'analysis']):
                quality_score += 0.3
                quality_indicators.append("Contains research or data")
            
            # Check for specific metrics
            if any(metric in ev_lower for metric in ['percent', '%', 'tons', 'kg', 'liters', 'kwh']):
                quality_score += 0.2
                quality_indicators.append("Contains specific metrics")
            
            # Check for third-party verification
            if any(verifier in ev_lower for verifier in ['certified', 'verified', 'audited', 'third-party']):
                quality_score += 0.3
                quality_indicators.append("Third-party verification mentioned")
            
            # Check for recent information
            if any(year in ev_lower for year in ['2023', '2022', '2021', '2020']):
                quality_score += 0.2
                quality_indicators.append("Recent information provided")
        
        return {
            'score': min(1.0, quality_score),
            'indicators': quality_indicators
        }
