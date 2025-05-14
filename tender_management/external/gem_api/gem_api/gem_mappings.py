# -*- coding: utf-8 -*-

import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

def map_gem_tender_to_odoo(gem_tender, detailed=False):
    """
    Map GeM tender data to Odoo tender.bid fields.
    
    Args:
        gem_tender: Dictionary with GeM tender data
        detailed: Whether this is a detailed tender view
        
    Returns:
        dict: Mapped values for Odoo tender.bid
    """
    # Basic mapping for search results
    mapped_data = {
        'name': gem_tender.get('title', ''),
        'reference': gem_tender.get('bid_number', ''),
        'gem_bid_id': gem_tender.get('id', ''),
        'submission_date': datetime.strptime(gem_tender.get('start_date', ''), '%Y-%m-%d') if gem_tender.get('start_date') else False,
        'closing_date': datetime.strptime(gem_tender.get('end_date', ''), '%Y-%m-%d') if gem_tender.get('end_date') else False,
        'estimated_value': float(gem_tender.get('estimated_value', 0.0)),
        'currency_id': map_currency_code(gem_tender.get('currency', 'INR')),
        'organization_name': gem_tender.get('buyer_name', ''),
        'gem_last_updated': datetime.strptime(gem_tender.get('updated_at', ''), '%Y-%m-%dT%H:%M:%SZ') if gem_tender.get('updated_at') else datetime.now(),
        'is_active': gem_tender.get('status') == 'ACTIVE',
    }
    
    # Additional fields for detailed view
    if detailed:
        mapped_data.update({
            'description': gem_tender.get('description', ''),
            'location': gem_tender.get('delivery_location', ''),
            'category': gem_tender.get('category_name', ''),
            'subcategory': gem_tender.get('subcategory_name', ''),
            'gem_status': gem_tender.get('status', ''),
            'gem_type': gem_tender.get('bid_type', ''),
            'min_qualification': gem_tender.get('min_qualification', ''),
            'delivery_period': gem_tender.get('delivery_period', 0),
            'payment_terms': gem_tender.get('payment_terms', ''),
        })
        
        # Map requirements if available
        if 'requirements' in gem_tender:
            requirements = []
            for req in gem_tender['requirements']:
                requirements.append({
                    'name': req.get('title', ''),
                    'description': req.get('description', ''),
                    'is_mandatory': req.get('is_mandatory', False),
                    'external_id': req.get('id', ''),
                })
            mapped_data['requirements'] = requirements
            
        # Map documents if available
        if 'documents' in gem_tender:
            documents = []
            for doc in gem_tender['documents']:
                documents.append({
                    'name': doc.get('name', ''),
                    'type': doc.get('type', ''),
                    'external_id': doc.get('id', ''),
                    'size': doc.get('size', 0),
                    'mimetype': doc.get('mime_type', 'application/pdf'),
                })
            mapped_data['documents'] = documents
    
    return mapped_data

def map_odoo_application_to_gem(tender_application):
    """
    Map Odoo tender.application data to GeM bid submission format.
    
    Args:
        tender_application: tender.application record
        
    Returns:
        dict: Mapped values for GeM API
    """
    tender_bid = tender_application.bid_id
    
    # Basic bid submission data
    mapped_data = {
        'bid_id': tender_bid.gem_bid_id,
        'application_ref': tender_application.name,
        'price_details': {
            'base_price': tender_application.amount,
            'currency': get_currency_code(tender_application.currency_id),
            'tax_amount': tender_application.tax_amount,
            'total_amount': tender_application.total_amount,
        },
        'technical_compliance': [],
        'seller_details': {
            'seller_name': tender_application.company_id.name,
            'seller_id': tender_application.company_id.vat or '',  # Using VAT as seller ID
            'contact_person': tender_application.user_id.name,
            'email': tender_application.user_id.email,
            'phone': tender_application.user_id.phone or '',
        },
        'delivery_details': {
            'delivery_period': tender_application.delivery_period,
            'delivery_terms': tender_application.delivery_terms or '',
        },
        'other_details': {
            'remarks': tender_application.note or '',
        }
    }
    
    # Add technical compliance details
    if tender_application.requirement_responses:
        for response in tender_application.requirement_responses:
            mapped_data['technical_compliance'].append({
                'requirement_id': response.requirement_id.external_id,
                'compliance_status': 'COMPLIANT' if response.is_compliant else 'NON_COMPLIANT',
                'response_text': response.response_text or '',
                'remarks': response.remarks or '',
            })
    
    # Add document references
    if tender_application.document_ids:
        mapped_data['documents'] = []
        for doc in tender_application.document_ids:
            mapped_data['documents'].append({
                'document_id': doc.external_id if doc.external_id else '',
                'document_type': doc.type,
                'document_name': doc.name,
            })
    
    return mapped_data

def map_currency_code(currency_code):
    """
    Map currency code to Odoo currency ID.
    
    Args:
        currency_code: ISO currency code
        
    Returns:
        int: Odoo currency ID
    """
    # This would typically query the Odoo database to find the currency ID
    # For now, we'll return a placeholder value
    # In a real implementation, this would be:
    # return self.env['res.currency'].search([('name', '=', currency_code)], limit=1).id
    return 1  # Placeholder - would be replaced with actual implementation

def get_currency_code(currency_id):
    """
    Get currency code from Odoo currency ID.
    
    Args:
        currency_id: Odoo currency record
        
    Returns:
        str: ISO currency code
    """
    # In a real implementation, this would return currency_id.name
    # For this example, default to INR
    return 'INR'
