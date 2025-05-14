from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """
    Handle post-migration tasks for upgrading from 17.0.1.0.0 to 17.0.1.1.0.
    This migration adds AI analytics functionality and enhances GeM integration.
    """
    if not version:
        # Skip if this is a fresh install
        return
    
    # Add new GeM integration features
    if openupgrade.column_exists(env.cr, 'tender_tender', 'gem_bid_no') and not openupgrade.column_exists(env.cr, 'tender_tender', 'gem_bid_url'):
        # Add gem_bid_url column
        openupgrade.add_columns(
            env.cr,
            {'tender_tender': [
                ('gem_bid_url', 'varchar', None, None, 'URL to the GeM bid')
            ]}
        )
        
        # Populate gem_bid_url for existing records
        env.cr.execute("""
            UPDATE tender_tender
            SET gem_bid_url = 'https://gem.gov.in/bid/' || gem_bid_no
            WHERE gem_bid_no IS NOT NULL AND gem_bid_url IS NULL
        """)
    
    # Create AI analyzer configuration
    ai_config = env['ir.config_parameter'].sudo().get_param('tender_management.ai_analyzer_enabled')
    if not ai_config:
        env['ir.config_parameter'].sudo().set_param('tender_management.ai_analyzer_enabled', 'False')
        env['ir.config_parameter'].sudo().set_param('tender_management.ai_analyzer_endpoint', 'http://localhost:8000/analyze')
        
    # Set up demo data for analytics if in demo mode
    if env['ir.module.module'].search([('name', '=', 'tender_management'), ('demo', '=', True)]):
        # Create demo dashboard
        if not env['tender.dashboard'].search([('name', '=', 'Demo Dashboard')]):
            dashboard = env['tender.dashboard'].create({
                'name': 'Demo Dashboard',
                'user_id': env.ref('base.user_admin').id,
                'dashboard_type': 'comprehensive',
            })
            dashboard.action_generate_data()
    
    # Update tender success prediction model
    if openupgrade.table_exists(env.cr, 'tender_success_model'):
        # Check if prediction model data exists
        if not env['tender.success.model'].search_count([]):
            # Create initial model parameters
            env['tender.success.model'].create({
                'name': 'Default Success Prediction Model',
                'active': True,
                'model_version': '1.0',
                'last_trained_date': openupgrade.fields.Datetime.now(),
                'accuracy': 0.85,
                'parameters': """
                {
                    "price_weight": 0.4,
                    "technical_weight": 0.3,
                    "past_performance_weight": 0.2,
                    "delivery_time_weight": 0.1
                }
                """
            })
    
    # Set up OCR service configuration
    ocr_config = env['ir.config_parameter'].sudo().get_param('tender_management.ocr_service_enabled')
    if not ocr_config:
        env['ir.config_parameter'].sudo().set_param('tender_management.ocr_service_enabled', 'False')
        env['ir.config_parameter'].sudo().set_param('tender_management.ocr_service_endpoint', 'http://localhost:8001/ocr')
    
    # Update menu structure
    if openupgrade.get_legacy_name('tender_menu_root') in env.registry:
        old_menu = env.ref(openupgrade.get_legacy_name('tender_menu_root'), raise_if_not_found=False)
        new_menu = env.ref('tender_management.tender_menu_root', raise_if_not_found=False)
        if old_menu and new_menu:
            # Transfer menu properties
            new_menu.write({
                'sequence': old_menu.sequence,
                'groups_id': [(6, 0, old_menu.groups_id.ids)]
            })
    
    # Log migration completion
    openupgrade.logging.getLogger('openupgrade').info(
        "Post-migration of tender_management to version 17.0.1.1.0 completed successfully"
    )
