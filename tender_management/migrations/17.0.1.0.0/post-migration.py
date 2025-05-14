from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """
    Handle post-migration tasks for tender_management module.
    This runs after the module has been updated.
    """
    if not version:
        # Skip if this is a fresh install
        return
    
    # Migrate data from old columns to new columns
    if openupgrade.column_exists(env.cr, 'tender_tender', 'state_old'):
        # Map old state values to new state values
        openupgrade.map_values(
            env.cr,
            'state_old', 'state',
            [
                ('draft', 'draft'),
                ('open', 'published'),
                ('in_progress', 'published'),
                ('close', 'closed'),
                ('done', 'awarded'),
                ('cancel', 'cancelled')
            ],
            table='tender_tender'
        )
        
        # Remove temporary column
        openupgrade.drop_columns(
            env.cr,
            {'tender_tender': ['state_old']}
        )
    
    # Populate new fields with default values
    env.cr.execute("""
        UPDATE tender_tender
        SET is_gem = False
        WHERE is_gem IS NULL
    """)
    
    # Create missing sequences
    sequence = env.ref('tender_management.sequence_tender_reference', raise_if_not_found=False)
    if sequence:
        # Update sequence with highest existing reference
        env.cr.execute("""
            SELECT MAX(CAST(regexp_replace(reference, '[^0-9]', '', 'g') AS INTEGER))
            FROM tender_tender
            WHERE reference ~ '[0-9]'
        """)
        result = env.cr.fetchone()
        if result and result[0]:
            sequence.number_next = result[0] + 1
    
    # Initialize new tables or fields
    if openupgrade.table_exists(env.cr, 'tender_analytics_config'):
        # Create default analytics configuration if none exists
        if not env['tender.analytics.config'].search_count([]):
            env['tender.analytics.config'].create({
                'name': 'Default Configuration',
                'active': True,
                'auto_refresh': True,
                'refresh_interval': 24,
            })
    
    # Update view architecture if needed
    view = env.ref('tender_management.view_tender_form', raise_if_not_found=False)
    if view:
        # Ensure the view has the new fields
        if 'is_gem' not in view.arch:
            arch = view.arch.replace(
                '<field name="state" widget="statusbar"/>', 
                '<field name="state" widget="statusbar"/>\n<field name="is_gem" invisible="1"/>'
            )
            view.write({'arch': arch})
    
    # Rebuild indexes for improved performance
    env.cr.execute("""
        REINDEX TABLE tender_tender;
        REINDEX TABLE tender_bid;
        REINDEX TABLE tender_document;
    """)
    
    # Update translations
    openupgrade.load_data(
        env.cr, 'tender_management', 'migrations/17.0.1.0.0/noupdate_changes.xml'
    )
    
    # Log migration completion
    openupgrade.logging.getLogger('openupgrade').info(
        "Post-migration of tender_management module completed successfully"
    )

