# __manifest__.py
{
    'name': 'Tender & GEM Bid Management',
    'version': '17.0.1.0.0',
    'summary': 'Comprehensive solution for managing tenders and GeM portal bids',
    'description': """
        This module provides a complete solution for managing tender processes
        and Government e-Marketplace (GeM) portal bids:
        
        * Complete tender lifecycle management
        * GeM portal integration
        * Automated bid preparation
        * Document management
        * OCR for tender document parsing
        * Analytics and reporting
        * Team collaboration tools
        * AI-powered assistant for bid preparation
    """,
    'category': 'Sales/Tenders',
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'sale_management',
        'purchase',
        'project',
        'document',
        'web',
        'portal',
        'attachment_indexation',
    ],
    'data': [
        # Security
        'security/tender_security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/tender_sequences.xml',
        'data/tender_data.xml',
        'data/tender_email_templates.xml',
        'data/tender_cron.xml',
        # Views
        'views/tender_views.xml',
        'views/tender_gem_views.xml',
        'views/tender_company_views.xml',
        'views/tender_department_views.xml',
        'views/tender_analytics_views.xml',
        'views/tender_ocr_views.xml',
        'views/tender_team_views.xml',
        'views/tender_document_views.xml',
        'views/tender_dashboard_views.xml',
        'views/tender_menus.xml',
        'views/tender_portal_templates.xml',
        # Wizards
        'wizards/tender_bid_wizard_views.xml',
        'wizards/tender_import_wizard_views.xml',
        # Reports
        'reports/paper_format.xml',
        'reports/tender_report_templates.xml',
        'reports/tender_analytics_report.xml',
        'reports/tender_bid_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tender_management/static/src/scss/tender_common.scss',
            'tender_management/static/src/scss/tender_dashboard.scss',
            'tender_management/static/src/scss/tender_chat.scss',
            'tender_management/static/src/js/tender_dashboard.js',
            'tender_management/static/src/js/tender_ai_chat.js',
            'tender_management/static/src/js/tender_widgets.js',
            'tender_management/static/src/xml/tender_components.xml',
        ],
        'web.assets_frontend': [
            'tender_management/static/src/js/tender_portal.js',
        ],
    },
    'demo': [
        'data/tender_demo.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 1,
    'external_dependencies': {
        'python': ['PyPDF2', 'pytesseract', 'openai', 'requests', 'beautifulsoup4'],
        'bin': ['tesseract'],
    },
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
}
