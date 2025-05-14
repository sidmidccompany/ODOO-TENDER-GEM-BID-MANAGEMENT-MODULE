from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """
    Handle pre-migration tasks for tender_management module.
    This runs before the module is updated.
    """
    if not version:
        # Skip if this is a fresh install
        return
    
    # Create temporary columns if upgrading from previous version
    if openupgrade.column_exists(env.cr, 'tender_tender', 'state'):
        # If we're migrating from a previous version and changing state field type
        openupgrade.rename_columns(
            env.cr,
            {'tender_tender': [('state', 'state_old')]}
        )
    
    # Back up data from tables that will be dropped or significantly modified
    if openupgrade.table_exists(env.cr, 'tender_tender'):
        # Backup tender data
        openupgrade.copy_columns(
            env.cr,
            {'tender_tender': [
                ('estimated_value', 'estimated_value_old', None),
                ('date_open', 'date_open_old', None),
            ]}
        )
    
    # Drop constraints that might interfere with the migration
    if openupgrade.table_exists(env.cr, 'tender_bid'):
        env.cr.execute("""
            SELECT conname
            FROM pg_constraint
            WHERE conrelid = 'tender_bid'::regclass
            AND conname LIKE 'tender_bid_%_check'
        """)
        for constraint in env.cr.fetchall():
            openupgrade.drop_constraint(
                env.cr,
                'tender_bid',
                constraint[0]
            )
    
    # Handle renaming of tables if any core object names are changing
    if openupgrade.table_exists(env.cr, 'tender_rfq') and not openupgrade.table_exists(env.cr, 'tender_bid'):
        openupgrade.rename_tables(
            env.cr,
            [('tender_rfq', 'tender_bid')]
        )
    
    # Update existing records to ensure they'll be compatible with new schema
    if openupgrade.table_exists(env.cr, 'tender_document'):
        env.cr.execute("""
            UPDATE tender_document
            SET document_type = 'other'
            WHERE document_type IS NULL
        """)
    
    # Log migration progress
    openupgrade.logging.getLogger('openupgrade').info(
        "Pre-migration of tender_management module completed successfully"
    )
