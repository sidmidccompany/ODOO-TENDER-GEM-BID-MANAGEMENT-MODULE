# -*- coding: utf-8 -*-

import base64
import json
import logging
import requests
from datetime import datetime
from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class AIAnalyzer:
    """
    This class integrates with AI services to analyze tender documents,
    extract key information, and assist in decision-making.
    """
    
    def __init__(self, env):
        """
        Initialize the AI Analyzer.
        
        Args:
            env: Odoo environment
        """
        self.env = env
        ICP = self.env['ir.config_parameter'].sudo()
        
        # Load configuration
        self.config = {
            'ai_service_url': ICP.get_param('tender_management.ai_service_url', ''),
            'ai_api_key': ICP.get_param('tender_management.ai_api_key', ''),
            'ai_provider': ICP.get_param('tender_management.ai_provider', 'openai'),
            'ai_enabled': ICP.get_param('tender_management.ai_enabled', 'False') == 'True',
            'ai_model': ICP.get_param('tender_management.ai_model', 'gpt-4'),
        }
        
        # Check if AI service is properly configured
        if not all([self.config['ai_service_url'], self.config['ai_api_key']]) and self.config['ai_enabled']:
            _logger.warning("AI service is enabled but not fully configured")
    
    def is_available(self):
        """
        Check if the AI service is available and properly configured.
        
        Returns:
            bool: True if available
        """
        return self.config['ai_enabled'] and all([self.config['ai_service_url'], self.config['ai_api_key']])
    
    def analyze_tender(self, tender_bid):
        """
        Analyze a tender bid and provide insights.
        
        Args:
            tender_bid: tender.bid record
            
        Returns:
            dict: Analysis results
        """
        if not self.is_available():
            raise UserError(_("AI analysis service is not properly configured or enabled."))
            
        # Prepare tender data for analysis
        tender_data = self._prepare_tender_data(tender_bid)
        
        # Select AI provider
        if self.config['ai_provider'] == 'openai':
            return self._analyze_with_openai(tender_data, "tender_analysis")
        elif self.config['ai_provider'] == 'azure_openai':
            return self._analyze_with_azure_openai(tender_data, "tender_analysis")
        elif self.config['ai_provider'] == 'google_vertex':
            return self._analyze_with_google_vertex(tender_data, "tender_analysis")
        else:
            return self._analyze_with_custom_ai(tender_data, "tender_analysis")
    
    def analyze_requirements(self, tender_bid):
        """
        Analyze tender requirements and provide insights.
        
        Args:
            tender_bid: tender.bid record
            
        Returns:
            dict: Analysis results
        """
        if not self.is_available():
            raise UserError(_("AI analysis service is not properly configured or enabled."))
            
        # Prepare requirements data for analysis
        requirements_data = self._prepare_requirements_data(tender_bid)
        
        # Select AI provider
        if self.config['ai_provider'] == 'openai':
            return self._analyze_with_openai(requirements_data, "requirements_analysis")
        elif self.config['ai_provider'] == 'azure_openai':
            return self._analyze_with_azure_openai(requirements_data, "requirements_analysis")
        elif self.config['ai_provider'] == 'google_vertex':
            return self._analyze_with_google_vertex(requirements_data, "requirements_analysis")
        else:
            return self._analyze_with_custom_ai(requirements_data, "requirements_analysis")
    
    def extract_requirements(self, document_text):
        """
        Extract requirements from tender document text.
        
        Args:
            document_text: Text of the tender document
            
        Returns:
            dict: Extracted requirements
        """
        if not self.is_available():
            raise UserError(_("AI analysis service is not properly configured or enabled."))
            
        # Prepare data for requirements extraction
        extraction_data = {
            'document_text': document_text,
            'task': 'extract_requirements',
        }
        
        # Select AI provider
        if self.config['ai_provider'] == 'openai':
            return self._analyze_with_openai(extraction_data, "requirements_extraction")
        elif self.config['ai_provider'] == 'azure_openai':
            return self._analyze_with_azure_openai(extraction_data, "requirements_extraction")
        elif self.config['ai_provider'] == 'google_vertex':
            return self._analyze_with_google_vertex(extraction_data, "requirements_extraction")
        else:
            return self._analyze_with_custom_ai(extraction_data, "requirements_extraction")
    
    def generate_bid_summary(self, tender_application):
        """
        Generate a summary of a tender application/bid.
        
        Args:
            tender_application: tender.application record
            
        Returns:
            dict: Generated summary
        """
        if not self.is_available():
            raise UserError(_("AI analysis service is not properly configured or enabled."))
            
        # Prepare application data for summary generation
        application_data = self._prepare_application_data(tender_application)
        
        # Select AI provider
        if self.config['ai_provider'] == 'openai':
            return self._analyze_with_openai(application_data, "bid_summary")
        elif self.config['ai_provider'] == 'azure_openai':
            return self._analyze_with_azure_openai(application_data, "bid_summary")
        elif self.config['ai_provider'] == 'google_vertex':
            return self._analyze_with_google_vertex(application_data, "bid_summary")
        else:
            return self._analyze_with_custom_ai(application_data, "bid_summary")
    
    def analyze_win_probability(self, tender_application):
        """
        Analyze the probability of winning a tender.
        
        Args:
            tender_application: tender.application record
            
        Returns:
            dict: Win probability analysis
        """
        if not self.is_available():
            raise UserError(_("AI analysis service is not properly configured or enabled."))
            
        # Prepare data for win probability analysis
        win_prob_data = self._prepare_win_probability_data(tender_application)
        
        # Select AI provider
        if self.config['ai_provider'] == 'openai':
            return self._analyze_with_openai(win_prob_data, "win_probability")
        elif self.config['ai_provider'] == 'azure_openai':
            return self._analyze_with_azure_openai(win_prob_data, "win_probability")
        elif self.config['ai_provider'] == 'google_vertex':
            return self._analyze_with_google_vertex(win_prob_data, "win_probability")
        else:
            return self._analyze_with_custom_ai(win_prob_data, "win_probability")
    
    def suggest_bid_improvements(self, tender_application):
        """
        Suggest improvements for a tender application.
        
        Args:
            tender_application: tender.application record
            
        Returns:
            dict: Suggested improvements
        """
        if not self.is_available():
            raise UserError(_("AI analysis service is not properly configured or enabled."))
            
        # Prepare data for improvement suggestions
        improvement_data = self._prepare_improvement_data(tender_application)
        
        # Select AI provider
        if self.config['ai_provider'] == 'openai':
            return self._analyze_with_openai(improvement_data, "bid_improvements")
        elif self.config['ai_provider'] == 'azure_openai':
            return self._analyze_with_azure_openai(improvement_data, "bid_improvements")
        elif self.config['ai_provider'] == 'google_vertex':
            return self._analyze_with_google_vertex(improvement_data, "bid_improvements")
        else:
            return self._analyze_with_custom_ai(improvement_data, "bid_improvements")
    
    def _prepare_tender_data(self, tender_bid):
        """
        Prepare tender data for AI analysis.
        
        Args:
            tender_bid: tender.bid record
            
        Returns:
            dict: Prepared data
        """
        tender_data = {
            'tender_id': tender_bid.reference,
            'name': tender_bid.name,
            'organization': tender_bid.organization_id.name if tender_bid.organization_id else '',
            'description': tender_bid.description or '',
            'submission_date': tender_bid.submission_date.strftime('%Y-%m-%d') if tender_bid.submission_date else '',
            'closing_date': tender_bid.closing_date.strftime('%Y-%m-%d') if tender_bid.closing_date else '',
            'estimated_value': tender_bid.estimated_value,
            'currency': tender_bid.currency_id.name if tender_bid.currency_id else 'INR',
            'type': tender_bid.type_id.name if tender_bid.type_id else '',
            'stage': tender_bid.stage_id.name if tender_bid.stage_id else '',
            'tags': [tag.name for tag in tender_bid.tag_ids] if tender_bid.tag_ids else [],
        }
        
        # Add requirements if available
        if tender_bid.requirement_ids:
            tender_data['requirements'] = []
            for req in tender_bid.requirement_ids:
                tender_data['requirements'].append({
                    'name': req.name,
                    'description': req.description or '',
                    'is_mandatory': req.is_mandatory,
                    'state': req.state,
                })
        
        # Add documents if available
        if tender_bid.document_ids:
            tender_data['documents'] = []
            for doc in tender_bid.document_ids:
                tender_data['documents'].append({
                    'name': doc.name,
                    'type': doc.type,
                    'date': doc.date.strftime('%Y-%m-%d') if doc.date else '',
                })
        
        return tender_data
    
    def _prepare_requirements_data(self, tender_bid):
        """
        Prepare requirements data for AI analysis.
        
        Args:
            tender_bid: tender.bid record
            
        Returns:
            dict: Prepared data
        """
        requirements_data = {
            'tender_id': tender_bid.reference,
            'name': tender_bid.name,
            'requirements': [],
        }
        
        # Add requirements
        if tender_bid.requirement_ids:
            for req in tender_bid.requirement_ids:
                requirements_data['requirements'].append({
                    'name': req.name,
                    'description': req.description or '',
                    'is_mandatory': req.is_mandatory,
                    'state': req.state,
                })
        
        return requirements_data
    
    def _prepare_application_data(self, tender_application):
        """
        Prepare application data for AI analysis.
        
        Args:
            tender_application: tender.application record
            
        Returns:
            dict: Prepared data
        """
        tender_bid = tender_application.bid_id
        
        application_data = {
            'application_id': tender_application.name,
            'tender_id': tender_bid.reference,
            'tender_name': tender_bid.name,
            'organization': tender_bid.organization_id.name if tender_bid.organization_id else '',
            'submission_date': tender_application.submission_date.strftime('%Y-%m-%d') if tender_application.submission_date else '',
            'amount': tender_application.amount,
            'currency': tender_application.currency_id.name if tender_application.currency_id else 'INR',
            'state': tender_application.state,
            'technical_details': tender_application.technical_details or '',
            'financial_details': tender_application.financial_details or '',
            'note': tender_application.note or '',
        }
        
        # Add requirement responses if available
        if tender_application.requirement_responses:
            application_data['requirement_responses'] = []
            for resp in tender_application.requirement_responses:
                application_data['requirement_responses'].append({
                    'requirement': resp.requirement_id.name,
                    'is_compliant': resp.is_compliant,
                    'response_text': resp.response_text or '',
                })
        
        return application_data
    
    def _prepare_win_probability_data(self, tender_application):
        """
        Prepare data for win probability analysis.
        
        Args:
            tender_application: tender.application record
            
        Returns:
            dict: Prepared data
        """
        tender_bid = tender_application.bid_id
        
        # Start with basic application data
        win_prob_data = self._prepare_application_data(tender_application)
        
        # Add historical bid data if available
        win_prob_data['historical_data'] = {
            'total_bids': 0,
            'won_bids': 0,
            'similar_bids': [],
        }
        
        # In a real implementation, we would query historical data from the database
        # For now, we'll use placeholder data
        TenderApplication = self.env['tender.application']
        
        # Get total bids and won bids for the same organization
        if tender_bid.organization_id:
            domain = [
                ('bid_id.organization_id', '=', tender_bid.organization_id.id),
                ('state', 'in', ['won', 'lost']),  # Only consider completed bids
            ]
            total_bids = TenderApplication.search_count(domain)
            won_bids = TenderApplication.search_count(domain + [('state', '=', 'won')])
            
            win_prob_data['historical_data']['total_bids'] = total_bids
            win_prob_data['historical_data']['won_bids'] = won_bids
            
            # Get similar bids (same organization and type)
            if tender_bid.type_id:
                similar_domain = domain + [('bid_id.type_id', '=', tender_bid.type_id.id)]
                similar_bids = TenderApplication.search(similar_domain, limit=5)
                
                similar_bid_data = []
                for bid in similar_bids:
                    similar_bid_data.append({
                        'tender_name': bid.bid_id.name,
                        'amount': bid.amount,
                        'state': bid.state,
                        'submission_date': bid.submission_date.strftime('%Y-%m-%d') if bid.submission_date else '',
                    })
                
                win_prob_data['historical_data']['similar_bids'] = similar_bid_data
        
        return win_prob_data
    
    def _prepare_improvement_data(self, tender_application):
        """
        Prepare data for improvement suggestions.
        
        Args:
            tender_application: tender.application record
            
        Returns:
            dict: Prepared data
        """
        # Start with basic application data
        improvement_data = self._prepare_application_data(tender_application)
        
        # Add requirements that are not fully compliant
        if tender_application.requirement_responses:
            improvement_data['non_compliant_requirements'] = []
            for resp in tender_application.requirement_responses:
                if not resp.is_compliant:
                    improvement_data['non_compliant_requirements'].append({
                        'requirement': resp.requirement_id.name,
                        'description': resp.requirement_id.description or '',
                        'is_mandatory': resp.requirement_id.is_mandatory,
                        'response_text': resp.response_text or '',
                    })
        
        # Add successful applications for similar tenders if available
        improvement_data['successful_applications'] = []
        
        # In a real implementation, we would query successful applications from the database
        # For now, we'll use placeholder data
        
        return improvement_data
    
    def _analyze_with_openai(self, data, analysis_type):
        """
        Analyze data using OpenAI API.
        
        Args:
            data: Data to analyze
            analysis_type: Type of analysis to perform
            
        Returns:
            dict: Analysis results
        """
        try:
            endpoint = f"{self.config['ai_service_url']}/v1/chat/completions"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {self.config['ai_api_key']}"
            }
            
            # Create appropriate system prompt based on analysis type
            system_prompt = self._get_system_prompt(analysis_type)
            
            # Prepare the request payload
            payload = {
                "model": self.config['ai_model'],
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(data)}
                ],
                "temperature": 0.2,  # Lower temperature for more deterministic results
                "max_tokens": 1500,
                "response_format": {"type": "json_object"}
            }
            
            # Make the API request
            response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                response_data = response.json()
                
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    result_content = response_data['choices'][0]['message']['content']
                    try:
                        result_json = json.loads(result_content)
                        result_json['success'] = True
                        return result_json
                    except json.JSONDecodeError:
                        _logger.error(f"Failed to parse OpenAI response as JSON: {result_content}")
                        return {
                            'success': False,
                            'error': 'Failed to parse AI response as JSON',
                            'raw_response': result_content
                        }
                
                return {
                    'success': False,
                    'error': 'No valid response from OpenAI API',
                    'raw_response': response_data
                }
            else:
                error_msg = f"OpenAI API Error: {response.status_code} - {response.text}"
                _logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            error_msg = f"OpenAI analysis error: {str(e)}"
            _logger.exception(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def _analyze_with_azure_openai(self, data, analysis_type):
        """
        Analyze data using Azure OpenAI API.
        
        Args:
            data: Data to analyze
            analysis_type: Type of analysis to perform
            
        Returns:
            dict: Analysis results
        """
        try:
            # Parse Azure OpenAI URL to extract resource name and deployment ID
            url_parts = self.config['ai_service_url'].split('/')
            if len(url_parts) >= 7:
                resource_name = url_parts[2].split('.')[0]
                deployment_id = url_parts[6]
                endpoint = f"https://{resource_name}.openai.azure.com/openai/deployments/{deployment_id}/chat/completions?api-version=2023-05-15"
            else:
                endpoint = self.config['ai_service_url']
            
            headers = {
                'Content-Type': 'application/json',
                'api-key': self.config['ai_api_key']
            }
            
            # Create appropriate system prompt based on analysis type
            system_prompt = self._get_system_prompt(analysis_type)
            
            # Prepare the request payload
            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(data)}
                ],
                "temperature": 0.2,  # Lower temperature for more deterministic results
                "max_tokens": 1500,
                "response_format": {"type": "json_object"}
            }
            
            # Make the API request
            response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                response_data = response.json()
                
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    result_content = response_data['choices'][0]['message']['content']
                    try:
                        result_json = json.loads(result_content)
                        result_json['success'] = True
                        return result_json
                    except json.JSONDecodeError:
                        _logger.error(f"Failed to parse Azure OpenAI response as JSON: {result_content}")
                        return {
                            'success': False,
                            'error': 'Failed to parse AI response as JSON',
                            'raw_response': result_content
                        }
                
                return {
                    'success': False,
                    'error': 'No valid response from Azure OpenAI API',
                    'raw_response': response_data
                }
            else:
                error_msg = f"Azure OpenAI API Error: {response.status_code} - {response.text}"
                _logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            error_msg = f"Azure OpenAI analysis error: {str(e)}"
            _logger.exception(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def _analyze_with_google_vertex(self, data, analysis_type):
        """
        Analyze data using Google Vertex AI API.
        
        Args:
            data: Data to analyze
            analysis_type: Type of analysis to perform
            
        Returns:
            dict: Analysis results
        """
        try:
            endpoint = f"{self.config['ai_service_url']}"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {self.config['ai_api_key']}"
            }
            
            # Create appropriate system prompt based on analysis type
            system_prompt = self._get_system_prompt(analysis_type)
            
            # Prepare the request payload for Vertex AI
            payload = {
                "contents": [
                    {"role": "system", "parts": [{"text": system_prompt}]},
                    {"role": "user", "parts": [{"text": json.dumps(data)}]}
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 1500,
                    "responseMimeType": "application/json"
                }
            }
            
            # Make the API request
            response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                response_data = response.json()
                
                if 'candidates' in response_data and len(response_data['candidates']) > 0:
                    result_content = response_data['candidates'][0]['content']['parts'][0]['text']
                    try:
                        result_json = json.loads(result_content)
                        result_json['success'] = True
                        return result_json
                    except json.JSONDecodeError:
                        _logger.error(f"Failed to parse Google Vertex AI response as JSON: {result_content}")
                        return {
                            'success': False,
                            'error': 'Failed to parse AI response as JSON',
                            'raw_response': result_content
                        }
                
                return {
                    'success': False,
                    'error': 'No valid response from Google Vertex AI API',
                    'raw_response': response_data
                }
            else:
                error_msg = f"Google Vertex AI API Error: {response.status_code} - {response.text}"
                _logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            error_msg = f"Google Vertex AI analysis error: {str(e)}"
            _logger.exception(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def _analyze_with_custom_ai(self, data, analysis_type):
        """
        Analyze data using a custom AI service.
        
        Args:
            data: Data to analyze
            analysis_type: Type of analysis to perform
            
        Returns:
            dict: Analysis results
        """
        try:
            endpoint = self.config['ai_service_url']
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {self.config['ai_api_key']}"
            }
            
            # Create appropriate system prompt based on analysis type
            system_prompt = self._get_system_prompt(analysis_type)
            
            # Prepare the request payload
            payload = {
                "system_prompt": system_prompt,
                "user_input": json.dumps(data),
                "analysis_type": analysis_type,
                "options": {
                    "temperature": 0.2,
                    "max_tokens": 1500,
                    "response_format": "json"
                }
            }
            
            # Make the API request
            response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                response_data = response.json()
                
                if 'result' in response_data:
                    try:
                        if isinstance(response_data['result'], str):
                            result_json = json.loads(response_data['result'])
                        else:
                            result_json = response_data['result']
                        
                        result_json['success'] = True
                        return result_json
                    except json.JSONDecodeError:
                        _logger.error(f"Failed to parse custom AI response as JSON: {response_data['result']}")
                        return {
                            'success': False,
                            'error': 'Failed to parse AI response as JSON',
                            'raw_response': response_data['result']
                        }
                
                return {
                    'success': False,
                    'error': 'No valid result in custom AI API response',
                    'raw_response': response_data
                }
            else:
                error_msg = f"Custom AI API Error: {response.status_code} - {response.text}"
                _logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            error_msg = f"Custom AI analysis error: {str(e)}"
            _logger.exception(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def _get_system_prompt(self, analysis_type):
        """
        Get appropriate system prompt based on analysis type.
        
        Args:
            analysis_type: Type of analysis to perform
            
        Returns:
            str: System prompt
        """
        if analysis_type == "tender_analysis":
            return """
            You are an expert in tender analysis. Analyze the provided tender data and provide insights.
            Focus on key aspects such as requirements, deadlines, estimated value, and potential challenges.
            Identify any red flags or opportunities. Format your response as a structured JSON with:
            1. "summary": A brief overview of the tender.
            2. "key_points": A list of the most important aspects.
            3. "opportunities": Potential advantages or opportunities.
            4. "challenges": Potential difficulties or challenges.
            5. "recommended_action": Recommended next steps.
            6. "priority_level": A rating from 1-5 of how much priority this tender should receive.
            """
        
        elif analysis_type == "requirements_analysis":
            return """
            You are an expert in analyzing tender requirements. Review the provided requirements list and provide insights.
            Identify any challenging requirements, vague specifications, or potential compliance issues.
            Format your response as a structured JSON with:
            1. "summary": Brief overview of requirements complexity.
            2. "challenging_requirements": List of potentially difficult requirements with reasoning.
            3. "vague_requirements": List of unclear or ambiguous requirements that need clarification.
            4. "compliance_challenges": Potential compliance issues to address.
            5. "recommended_actions": Specific actions to address identified issues.
            """
        
        elif analysis_type == "requirements_extraction":
            return """
            You are an expert in extracting structured requirements from tender documents.
            Analyze the provided document text and extract all requirements, categorizing them as technical, financial, eligibility, etc.
            Format your response as a structured JSON with:
            1. "total_requirements": Total number of extracted requirements.
            2. "requirements": A list of requirement objects, each with:
               - "name": A concise name for the requirement
               - "description": Detailed description of the requirement
               - "category": Type of requirement (technical, financial, eligibility, etc.)
               - "is_mandatory": Boolean indicating if it appears to be mandatory
               - "section": Document section where the requirement was found
            """
        
        elif analysis_type == "bid_summary":
            return """
            You are an expert in summarizing tender bids/applications. Create a comprehensive summary of the provided bid data.
            Format your response as a structured JSON with:
            1. "executive_summary": A brief overview of the bid (2-3 sentences).
            2. "financial_summary": Key financial aspects of the bid.
            3. "technical_summary": Summary of technical aspects and compliance.
            4. "strengths": Key strengths of the application.
            5. "weaknesses": Areas that could be improved.
            6. "overall_assessment": Brief overall assessment of the application quality.
            """
        
        elif analysis_type == "win_probability":
            return """
            You are an expert in assessing tender win probability. Analyze the provided bid data and historical information.
            Format your response as a structured JSON with:
            1. "win_probability_percentage": Estimated probability of winning (0-100%).
            2. "key_factors": List of factors influencing the probability, each with:
               - "factor": Name of factor
               - "impact": Positive or negative impact
               - "weight": Relative importance (high, medium, low)
            3. "comparison_to_historical": How this bid compares to historical bids.
            4. "recommendations": Suggestions to increase win probability.
            5. "confidence_level": Confidence in this assessment (high, medium, low).
            """
        
        elif analysis_type == "bid_improvements":
            return """
            You are an expert in improving tender bids. Analyze the provided bid data and suggest improvements.
            Format your response as a structured JSON with:
            1. "overall_assessment": Brief assessment of current application quality.
            2. "technical_improvements": List of suggested improvements to technical aspects.
            3. "financial_improvements": Suggestions for financial aspects.
            4. "document_improvements": Recommendations for documentation.
            5. "compliance_improvements": Suggestions to improve compliance with requirements.
            6. "priority_improvements": List of highest-priority improvements to focus on.
            """
        
        else:
            # Default generic prompt
            return """
            You are an expert in tender management and analysis. Review the provided data and provide valuable insights
            in JSON format. Focus on practical, actionable information that would help with tender decision-making.
            """
