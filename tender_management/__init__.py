# __init__.py
from . import models
from . import controllers
from . import wizards
from . import external

def post_init_hook(cr, registry):
    """Post-installation hook to set up initial data"""
    from odoo import api, SUPERUSER_ID
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Create default company profile if none exists
    if not env['tender.company'].search([]):
        company = env.user.company_id
        env['tender.company'].create({
            'name': f"{company.name} - Tender Profile",
            'legal_name': company.name,
            'company_id': company.id,
            'street': company.street,
            'street2': company.street2,
            'city': company.city,
            'state_id': company.state_id.id,
            'zip': company.zip,
            'country_id': company.country_id.id,
            'phone': company.phone,
            'email': company.email,
            'website': company.website,
        })
    
    # Create default departments
    if not env['tender.department'].search([]):
        departments = [
            ('Sales', 'SALES'),
            ('Procurement', 'PROC'),
            ('Technical', 'TECH'),
            ('Finance', 'FIN'),
            ('Legal', 'LEGAL')
        ]
        
        for name, code in departments:
            env['tender.department'].create({
                'name': name,
                'code': code,
                'company_id': env.user.company_id.id,
            })

def uninstall_hook(cr, registry):
    """Clean up on module uninstallation"""
    # No special cleanup needed
    pass
