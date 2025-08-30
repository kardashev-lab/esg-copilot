import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

class MaterialityAssessment:
    """Service for conducting materiality assessments and stakeholder engagement"""
    
    def __init__(self):
        self.esg_topics = {
            'environmental': [
                'climate_change', 'energy_efficiency', 'renewable_energy', 'water_management',
                'waste_management', 'biodiversity', 'air_quality', 'land_use',
                'circular_economy', 'sustainable_materials', 'emissions_reduction',
                'environmental_compliance', 'natural_resources', 'pollution_prevention'
            ],
            'social': [
                'labor_rights', 'human_rights', 'diversity_inclusion', 'health_safety',
                'training_development', 'community_engagement', 'supply_chain_labor',
                'product_safety', 'data_privacy', 'customer_satisfaction',
                'stakeholder_engagement', 'social_impact', 'accessibility',
                'fair_compensation', 'work_life_balance'
            ],
            'governance': [
                'board_diversity', 'executive_compensation', 'business_ethics',
                'anti_corruption', 'risk_management', 'compliance', 'transparency',
                'stakeholder_rights', 'tax_strategy', 'political_engagement',
                'data_security', 'cybersecurity', 'regulatory_compliance',
                'internal_controls', 'audit_quality'
            ]
        }
        
        self.stakeholder_groups = [
            'employees', 'customers', 'investors', 'suppliers', 'communities',
            'regulators', 'nongovernmental_organizations', 'academia', 'media',
            'industry_associations', 'trade_unions', 'indigenous_peoples'
        ]
        
        self.impact_categories = {
            'financial': ['revenue', 'costs', 'assets', 'liabilities', 'cash_flow'],
            'operational': ['efficiency', 'productivity', 'quality', 'capacity'],
            'reputational': ['brand_value', 'stakeholder_trust', 'market_position'],
            'regulatory': ['compliance_costs', 'fines_penalties', 'licensing'],
            'strategic': ['business_model', 'competitive_position', 'growth']
        }
    
    async def conduct_materiality_assessment(self, 
                                           stakeholder_feedback: List[Dict[str, Any]],
                                           company_data: Dict[str, Any],
                                           industry_context: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct a comprehensive materiality assessment"""
        
        assessment_results = {
            'assessment_date': datetime.utcnow().isoformat(),
            'material_topics': [],
            'stakeholder_priorities': {},
            'financial_impact_analysis': {},
            'materiality_matrix': {},
            'recommendations': [],
            'next_steps': []
        }
        
        # Analyze stakeholder feedback
        stakeholder_analysis = self._analyze_stakeholder_feedback(stakeholder_feedback)
        assessment_results['stakeholder_priorities'] = stakeholder_analysis
        
        # Analyze financial impact
        financial_analysis = self._analyze_financial_impact(company_data, industry_context)
        assessment_results['financial_impact_analysis'] = financial_analysis
        
        # Identify material topics
        material_topics = self._identify_material_topics(stakeholder_analysis, financial_analysis)
        assessment_results['material_topics'] = material_topics
        
        # Create materiality matrix
        materiality_matrix = self._create_materiality_matrix(material_topics)
        assessment_results['materiality_matrix'] = materiality_matrix
        
        # Generate recommendations
        assessment_results['recommendations'] = self._generate_materiality_recommendations(material_topics)
        
        # Define next steps
        assessment_results['next_steps'] = self._define_next_steps(material_topics)
        
        return assessment_results
    
    def _analyze_stakeholder_feedback(self, feedback: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze stakeholder feedback to identify priorities"""
        
        stakeholder_priorities = {
            'by_stakeholder_group': {},
            'by_topic': {},
            'overall_priorities': [],
            'engagement_levels': {}
        }
        
        # Initialize topic tracking
        topic_scores = {}
        for category, topics in self.esg_topics.items():
            for topic in topics:
                topic_scores[topic] = {
                    'total_score': 0,
                    'stakeholder_count': 0,
                    'average_score': 0,
                    'stakeholder_groups': []
                }
        
        # Process stakeholder feedback
        for response in feedback:
            stakeholder_group = response.get('stakeholder_group', 'unknown')
            topic_ratings = response.get('topic_ratings', {})
            
            if stakeholder_group not in stakeholder_priorities['by_stakeholder_group']:
                stakeholder_priorities['by_stakeholder_group'][stakeholder_group] = {
                    'top_priorities': [],
                    'average_engagement': 0,
                    'response_count': 0
                }
            
            # Track stakeholder group priorities
            group_data = stakeholder_priorities['by_stakeholder_group'][stakeholder_group]
            group_data['response_count'] += 1
            
            # Process topic ratings
            for topic, rating in topic_ratings.items():
                if topic in topic_scores:
                    topic_scores[topic]['total_score'] += rating
                    topic_scores[topic]['stakeholder_count'] += 1
                    if stakeholder_group not in topic_scores[topic]['stakeholder_groups']:
                        topic_scores[topic]['stakeholder_groups'].append(stakeholder_group)
        
        # Calculate average scores
        for topic, data in topic_scores.items():
            if data['stakeholder_count'] > 0:
                data['average_score'] = data['total_score'] / data['stakeholder_count']
        
        # Identify top priorities by stakeholder group
        for group, data in stakeholder_priorities['by_stakeholder_group'].items():
            group_topics = []
            for topic, topic_data in topic_scores.items():
                if group in topic_data['stakeholder_groups']:
                    group_topics.append((topic, topic_data['average_score']))
            
            # Sort by score and take top 5
            group_topics.sort(key=lambda x: x[1], reverse=True)
            data['top_priorities'] = group_topics[:5]
        
        # Overall priorities
        overall_topics = [(topic, data['average_score']) for topic, data in topic_scores.items()]
        overall_topics.sort(key=lambda x: x[1], reverse=True)
        stakeholder_priorities['overall_priorities'] = overall_topics[:10]
        
        # Topic analysis
        stakeholder_priorities['by_topic'] = topic_scores
        
        return stakeholder_priorities
    
    def _analyze_financial_impact(self, company_data: Dict[str, Any], 
                                industry_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze financial impact of ESG topics"""
        
        financial_analysis = {
            'high_impact_topics': [],
            'medium_impact_topics': [],
            'low_impact_topics': [],
            'impact_scores': {},
            'risk_opportunity_analysis': {}
        }
        
        # Analyze each ESG topic for financial impact
        for category, topics in self.esg_topics.items():
            for topic in topics:
                impact_score = self._calculate_financial_impact_score(topic, company_data, industry_context)
                financial_analysis['impact_scores'][topic] = impact_score
                
                # Categorize by impact level
                if impact_score >= 0.7:
                    financial_analysis['high_impact_topics'].append(topic)
                elif impact_score >= 0.4:
                    financial_analysis['medium_impact_topics'].append(topic)
                else:
                    financial_analysis['low_impact_topics'].append(topic)
                
                # Analyze risks and opportunities
                risk_opp_analysis = self._analyze_risks_opportunities(topic, company_data, industry_context)
                financial_analysis['risk_opportunity_analysis'][topic] = risk_opp_analysis
        
        return financial_analysis
    
    def _calculate_financial_impact_score(self, topic: str, company_data: Dict[str, Any], 
                                        industry_context: Dict[str, Any]) -> float:
        """Calculate financial impact score for a specific topic"""
        
        score = 0.0
        factors = 0
        
        # Industry relevance
        industry_relevance = industry_context.get('topic_relevance', {}).get(topic, 0.5)
        score += industry_relevance * 0.3
        factors += 1
        
        # Company exposure
        company_exposure = company_data.get('topic_exposure', {}).get(topic, 0.5)
        score += company_exposure * 0.3
        factors += 1
        
        # Regulatory pressure
        regulatory_pressure = industry_context.get('regulatory_pressure', {}).get(topic, 0.5)
        score += regulatory_pressure * 0.2
        factors += 1
        
        # Market demand
        market_demand = industry_context.get('market_demand', {}).get(topic, 0.5)
        score += market_demand * 0.2
        factors += 1
        
        return score / factors if factors > 0 else 0.0
    
    def _analyze_risks_opportunities(self, topic: str, company_data: Dict[str, Any], 
                                   industry_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze risks and opportunities for a specific topic"""
        
        analysis = {
            'risks': [],
            'opportunities': [],
            'risk_score': 0.0,
            'opportunity_score': 0.0
        }
        
        # Identify risks
        risks = self._identify_topic_risks(topic, company_data, industry_context)
        analysis['risks'] = risks
        
        # Identify opportunities
        opportunities = self._identify_topic_opportunities(topic, company_data, industry_context)
        analysis['opportunities'] = opportunities
        
        # Calculate scores
        analysis['risk_score'] = len(risks) * 0.2  # Simple scoring
        analysis['opportunity_score'] = len(opportunities) * 0.2
        
        return analysis
    
    def _identify_topic_risks(self, topic: str, company_data: Dict[str, Any], 
                            industry_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify specific risks for a topic"""
        
        risks = []
        
        # Generic risk patterns based on topic
        risk_patterns = {
            'climate_change': [
                'Regulatory compliance costs',
                'Physical asset risks',
                'Transition risks',
                'Reputational risks'
            ],
            'labor_rights': [
                'Legal compliance risks',
                'Supply chain disruption',
                'Reputational damage',
                'Operational risks'
            ],
            'data_privacy': [
                'Regulatory fines',
                'Customer trust loss',
                'Operational disruption',
                'Legal liability'
            ]
        }
        
        # Add topic-specific risks
        if topic in risk_patterns:
            for risk in risk_patterns[topic]:
                risks.append({
                    'risk': risk,
                    'severity': 'medium',
                    'probability': 'medium',
                    'mitigation': f'Implement {topic} management program'
                })
        
        return risks
    
    def _identify_topic_opportunities(self, topic: str, company_data: Dict[str, Any], 
                                    industry_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify specific opportunities for a topic"""
        
        opportunities = []
        
        # Generic opportunity patterns based on topic
        opportunity_patterns = {
            'renewable_energy': [
                'Cost savings through energy efficiency',
                'Market differentiation',
                'Regulatory incentives',
                'Customer preference'
            ],
            'diversity_inclusion': [
                'Improved innovation',
                'Better talent attraction',
                'Enhanced reputation',
                'Market expansion'
            ],
            'circular_economy': [
                'Resource efficiency gains',
                'Cost reduction',
                'New business models',
                'Customer loyalty'
            ]
        }
        
        # Add topic-specific opportunities
        if topic in opportunity_patterns:
            for opportunity in opportunity_patterns[topic]:
                opportunities.append({
                    'opportunity': opportunity,
                    'potential_impact': 'medium',
                    'timeframe': '1-3 years',
                    'action_required': f'Develop {topic} strategy'
                })
        
        return opportunities
    
    def _identify_material_topics(self, stakeholder_analysis: Dict[str, Any], 
                                financial_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify material topics based on stakeholder and financial analysis"""
        
        material_topics = []
        
        # Combine stakeholder and financial perspectives
        for topic, stakeholder_score in stakeholder_analysis['overall_priorities']:
            financial_score = financial_analysis['impact_scores'].get(topic, 0.0)
            
            # Calculate combined materiality score
            materiality_score = (stakeholder_score * 0.6) + (financial_score * 0.4)
            
            # Determine materiality level
            if materiality_score >= 0.7:
                materiality_level = 'high'
            elif materiality_score >= 0.4:
                materiality_level = 'medium'
            else:
                materiality_level = 'low'
            
            material_topic = {
                'topic': topic,
                'materiality_level': materiality_level,
                'materiality_score': materiality_score,
                'stakeholder_score': stakeholder_score,
                'financial_score': financial_score,
                'stakeholder_groups': stakeholder_analysis['by_topic'][topic]['stakeholder_groups'],
                'risks': financial_analysis['risk_opportunity_analysis'][topic]['risks'],
                'opportunities': financial_analysis['risk_opportunity_analysis'][topic]['opportunities']
            }
            
            material_topics.append(material_topic)
        
        # Sort by materiality score
        material_topics.sort(key=lambda x: x['materiality_score'], reverse=True)
        
        return material_topics
    
    def _create_materiality_matrix(self, material_topics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create materiality matrix visualization data"""
        
        matrix_data = {
            'high_stakeholder_high_financial': [],
            'high_stakeholder_low_financial': [],
            'low_stakeholder_high_financial': [],
            'low_stakeholder_low_financial': []
        }
        
        for topic in material_topics:
            stakeholder_score = topic['stakeholder_score']
            financial_score = topic['financial_score']
            
            if stakeholder_score >= 0.6 and financial_score >= 0.6:
                matrix_data['high_stakeholder_high_financial'].append(topic)
            elif stakeholder_score >= 0.6 and financial_score < 0.6:
                matrix_data['high_stakeholder_low_financial'].append(topic)
            elif stakeholder_score < 0.6 and financial_score >= 0.6:
                matrix_data['low_stakeholder_high_financial'].append(topic)
            else:
                matrix_data['low_stakeholder_low_financial'].append(topic)
        
        return matrix_data
    
    def _generate_materiality_recommendations(self, material_topics: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on materiality assessment"""
        
        recommendations = []
        
        # High materiality topics
        high_materiality = [t for t in material_topics if t['materiality_level'] == 'high']
        if high_materiality:
            recommendations.append(f"Prioritize {len(high_materiality)} high-materiality topics for immediate action")
        
        # Stakeholder engagement
        stakeholder_coverage = set()
        for topic in material_topics:
            stakeholder_coverage.update(topic['stakeholder_groups'])
        
        if len(stakeholder_coverage) < 8:
            recommendations.append("Expand stakeholder engagement to include more diverse perspectives")
        
        # Risk management
        high_risk_topics = [t for t in material_topics if len(t['risks']) > 3]
        if high_risk_topics:
            recommendations.append(f"Develop risk mitigation strategies for {len(high_risk_topics)} high-risk topics")
        
        # Opportunity capture
        high_opportunity_topics = [t for t in material_topics if len(t['opportunities']) > 2]
        if high_opportunity_topics:
            recommendations.append(f"Develop opportunity capture strategies for {len(high_opportunity_topics)} high-opportunity topics")
        
        # Reporting alignment
        recommendations.append("Align sustainability reporting with identified material topics")
        recommendations.append("Integrate material topics into business strategy and decision-making")
        recommendations.append("Establish regular materiality assessment review process")
        
        return recommendations
    
    def _define_next_steps(self, material_topics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Define next steps for materiality assessment implementation"""
        
        next_steps = []
        
        # Immediate actions (0-3 months)
        immediate_actions = []
        for topic in material_topics[:5]:  # Top 5 material topics
            immediate_actions.append({
                'action': f"Develop action plan for {topic['topic']}",
                'timeline': '0-3 months',
                'priority': 'high',
                'responsible': 'ESG team'
            })
        
        next_steps.append({
            'phase': 'Immediate Actions (0-3 months)',
            'actions': immediate_actions
        })
        
        # Short-term actions (3-12 months)
        short_term_actions = [
            {
                'action': 'Integrate material topics into business strategy',
                'timeline': '3-12 months',
                'priority': 'high',
                'responsible': 'Strategy team'
            },
            {
                'action': 'Develop stakeholder engagement program',
                'timeline': '3-12 months',
                'priority': 'medium',
                'responsible': 'Stakeholder relations'
            },
            {
                'action': 'Align sustainability reporting with material topics',
                'timeline': '3-12 months',
                'priority': 'medium',
                'responsible': 'Reporting team'
            }
        ]
        
        next_steps.append({
            'phase': 'Short-term Actions (3-12 months)',
            'actions': short_term_actions
        })
        
        # Long-term actions (1-3 years)
        long_term_actions = [
            {
                'action': 'Establish materiality assessment review process',
                'timeline': '1-3 years',
                'priority': 'medium',
                'responsible': 'ESG team'
            },
            {
                'action': 'Develop materiality-based performance metrics',
                'timeline': '1-3 years',
                'priority': 'medium',
                'responsible': 'Performance management'
            }
        ]
        
        next_steps.append({
            'phase': 'Long-term Actions (1-3 years)',
            'actions': long_term_actions
        })
        
        return next_steps
    
    async def conduct_stakeholder_engagement(self, engagement_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct stakeholder engagement activities"""
        
        engagement_results = {
            'engagement_date': datetime.utcnow().isoformat(),
            'stakeholder_responses': [],
            'engagement_summary': {},
            'feedback_analysis': {},
            'next_engagement_steps': []
        }
        
        # Mock stakeholder engagement process
        for stakeholder_group in engagement_plan.get('stakeholder_groups', []):
            response = self._simulate_stakeholder_response(stakeholder_group)
            engagement_results['stakeholder_responses'].append(response)
        
        # Analyze feedback
        engagement_results['feedback_analysis'] = self._analyze_engagement_feedback(
            engagement_results['stakeholder_responses']
        )
        
        # Generate engagement summary
        engagement_results['engagement_summary'] = self._generate_engagement_summary(
            engagement_results['stakeholder_responses']
        )
        
        # Define next steps
        engagement_results['next_engagement_steps'] = self._define_engagement_next_steps(
            engagement_results['feedback_analysis']
        )
        
        return engagement_results
    
    async def _process_stakeholder_response(self, stakeholder_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process actual stakeholder response data"""
        
        try:
            stakeholder_group = stakeholder_data.get('group', 'unknown')
            stakeholder_name = stakeholder_data.get('name', 'Unknown')
            
            # Process actual stakeholder response data
            response_data = stakeholder_data.get('response_data', {})
            
            # Extract priorities from response
            priorities = response_data.get('priorities', [])
            engagement_level = response_data.get('engagement_level', 'medium')
            feedback = response_data.get('feedback', 'No specific feedback provided')
            
            return {
                'stakeholder_group': stakeholder_group,
                'stakeholder_name': stakeholder_name,
                'response': {
                    'top_priorities': priorities,
                    'engagement_level': engagement_level,
                    'feedback': feedback
                },
                'response_date': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing stakeholder response: {e}")
            return {
                'stakeholder_group': stakeholder_data.get('group', 'unknown'),
                'stakeholder_name': stakeholder_data.get('name', 'Unknown'),
                'response': {
                    'top_priorities': ['general_esg'],
                    'engagement_level': 'low',
                    'feedback': 'Unable to process stakeholder response'
                },
                'response_date': datetime.utcnow().isoformat()
            }
    
    def _analyze_engagement_feedback(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze stakeholder engagement feedback"""
        
        analysis = {
            'engagement_levels': {},
            'priority_alignment': {},
            'feedback_themes': [],
            'action_items': []
        }
        
        # Analyze engagement levels
        for response in responses:
            group = response['stakeholder_group']
            level = response['response']['engagement_level']
            analysis['engagement_levels'][group] = level
        
        # Analyze priority alignment
        all_priorities = []
        for response in responses:
            all_priorities.extend(response['response']['top_priorities'])
        
        priority_counts = {}
        for priority in all_priorities:
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        analysis['priority_alignment'] = priority_counts
        
        # Identify feedback themes
        feedback_texts = [r['response']['feedback'] for r in responses]
        analysis['feedback_themes'] = self._extract_feedback_themes(feedback_texts)
        
        return analysis
    
    def _extract_feedback_themes(self, feedback_texts: List[str]) -> List[str]:
        """Extract common themes from feedback"""
        
        themes = []
        
        # Simple keyword-based theme extraction
        theme_keywords = {
            'safety': ['safety', 'health', 'security'],
            'development': ['development', 'training', 'growth', 'career'],
            'diversity': ['diversity', 'inclusion', 'equality'],
            'environment': ['environment', 'climate', 'sustainable'],
            'transparency': ['transparency', 'communication', 'disclosure']
        }
        
        for theme, keywords in theme_keywords.items():
            count = sum(1 for text in feedback_texts 
                       if any(keyword in text.lower() for keyword in keywords))
            if count > 0:
                themes.append(f"{theme}: mentioned in {count} responses")
        
        return themes
    
    def _generate_engagement_summary(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of stakeholder engagement"""
        
        summary = {
            'total_stakeholders': len(responses),
            'high_engagement': len([r for r in responses if r['response']['engagement_level'] == 'high']),
            'medium_engagement': len([r for r in responses if r['response']['engagement_level'] == 'medium']),
            'low_engagement': len([r for r in responses if r['response']['engagement_level'] == 'low']),
            'key_insights': []
        }
        
        # Generate key insights
        if summary['high_engagement'] > summary['total_stakeholders'] / 2:
            summary['key_insights'].append("Strong stakeholder engagement across groups")
        
        if summary['high_engagement'] < summary['total_stakeholders'] / 3:
            summary['key_insights'].append("Need to improve stakeholder engagement")
        
        return summary
    
    def _define_engagement_next_steps(self, feedback_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Define next steps for stakeholder engagement"""
        
        next_steps = []
        
        # Address low engagement
        low_engagement_groups = [
            group for group, level in feedback_analysis['engagement_levels'].items()
            if level == 'low'
        ]
        
        for group in low_engagement_groups:
            next_steps.append({
                'action': f'Improve engagement with {group}',
                'timeline': '3-6 months',
                'priority': 'high'
            })
        
        # Address priority alignment
        top_priorities = sorted(
            feedback_analysis['priority_alignment'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        for priority, count in top_priorities:
            next_steps.append({
                'action': f'Develop action plan for {priority}',
                'timeline': '6-12 months',
                'priority': 'medium'
            })
        
        return next_steps
