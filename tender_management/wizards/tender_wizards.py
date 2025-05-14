# wizards/tender_wizards.py
import base64
import tempfile
import logging
import io
import csv
import xlrd
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class TenderImportWizard(models.TransientModel):
    _name = 'tender.import.wizard'
    _description = 'Import Tenders'
    
    # Import Source
    import_type = fields.Selection([
        ('file', 'File Import (CSV/XLS)'),
        ('gem', 'GeM Portal'),
        ('url', 'Website URL')
    ], string='Import Source', default='file', required=True)
    
    # File Import Options
    file = fields.Binary(string='Import File')
    file_name = fields.Char(string='File Name')
    
    # GeM Portal Options
    gem_portal_id = fields.Many2one('gem.portal', string='GeM Portal')
    import_all = fields.Boolean(string='Import All Available Tenders', default=False)
    start_date = fields.Date(string='From Date')
    end_date = fields.Date(string='To Date')
    
    # URL Options
    url = fields.Char(string='Website URL')
    
    # Import Options
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    department_id = fields.Many2one('tender.department', string='Department')
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user)
    
    # Results
    import_log = fields.Text(string='Import Log', readonly=True)
    
    @api.onchange('import_type')
    def _onchange_import_type(self):
        """Reset fields based on import type"""
        self.file = False
        self.file_name = False
        self.gem_portal_id = False
        self.url = False
    
    def action_import(self):
        """Import tenders based on the selected import type"""
        self.ensure_one()
        
        if self.import_type == 'file':
            result = self._import_from_file()
        elif self.import_type == 'gem':
            result = self._import_from_gem()
        elif self.import_type == 'url':
            result = self._import_from_url()
        else:
            raise UserError(_("Invalid import type"))
        
        return result
    
    def _import_from_file(self):
        """Import tenders from a file"""
        if not self.file:
            raise UserError(_("Please select a file to import"))
        
        # Get file extension
        if self.file_name:
            file_ext = self.file_name.split('.')[-1].lower()
        else:
            file_ext = 'csv'  # Default to CSV
        
        # Process file based on extension
        if file_ext == 'csv':
            result = self._import_from_csv()
        elif file_ext in ['xls', 'xlsx']:
            result = self._import_from_excel()
        else:
            raise UserError(_("Unsupported file format. Please use CSV or Excel files."))
        
        return result
    
    def _import_from_csv(self):
        """Import tenders from a CSV file"""
        log = []
        created_count = 0
        updated_count = 0
        error_count = 0
        
        try:
            # Read CSV file
            file_data = base64.b64decode(self.file)
            file_input = io.StringIO(file_data.decode('utf-8'))
            reader = csv.DictReader(file_input)
            
            for row in reader:
                try:
                    # Map CSV columns to tender fields
                    tender_data = self._map_csv_to_tender(row)
                    
                    # Create or update tender
                    result = self._create_update_tender(tender_data)
                    
                    if result == 'created':
                        created_count += 1
                    elif result == 'updated':
                        updated_count += 1
                    
                except Exception as e:
                    error_count += 1
                    log.append(f"Error importing row {reader.line_num}: {str(e)}")
            
            # Summary log
            log.insert(0, _("Import Summary:"))
            log.insert(1, _("Tenders created: %s") % created_count)
            log.insert(2, _("Tenders updated: %s") % updated_count)
            log.insert(3, _("Errors: %s") % error_count)
            
            self.import_log = "\n".join(log)
            
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'tender.import.wizard',
                'view_mode': 'form',
                'res_id': self.id,
                'views': [(False, 'form')],
                'target': 'new',
            }
            
        except Exception as e:
            raise UserError(_("Error importing CSV file: %s") % str(e))
    
    def _import_from_excel(self):
        """Import tenders from an Excel file"""
        log = []
        created_count = 0
        updated_count = 0
        error_count = 0
        
        try:
            # Read Excel file
            file_data = base64.b64decode(self.file)
            book = xlrd.open_workbook(file_contents=file_data)
            sheet = book.sheet_by_index(0)
            
            # Read header row
            header = [sheet.cell_value(0, col) for col in range(sheet.ncols)]
            
            # Process data rows
            for row_idx in range(1, sheet.nrows):
                try:
                    # Create row dictionary from header
                    row = {}
                    for col_idx, key in enumerate(header):
                        cell_value = sheet.cell_value(row_idx, col_idx)
                        # Handle date cells
                        if sheet.cell_type(row_idx, col_idx) == xlrd.XL_CELL_DATE:
                            cell_value = xlrd.xldate_as_datetime(cell_value, book.datemode)
                        row[key] = cell_value
                    
                    # Map Excel columns to tender fields
                    tender_data = self._map_excel_to_tender(row)
                    
                    # Create or update tender
                    result = self._create_update_tender(tender_data)
                    
                    if result == 'created':
                        created_count += 1
                    elif result == 'updated':
                        updated_count += 1
                    
                except Exception as e:
                    error_count += 1
                    log.append(f"Error importing row {row_idx + 1}: {str(e)}")
            
            # Summary log
            log.insert(0, _("Import Summary:"))
            log.insert(1, _("Tenders created: %s") % created_count)
            log.insert(2, _("Tenders updated: %s") % updated_count)
            log.insert(3, _("Errors: %s") % error_count)
            
            self.import_log = "\n".join(log)
            
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'tender.import.wizard',
                'view_mode': 'form',
                'res_id': self.id,
                'views': [(False, 'form')],
                'target': 'new',
            }
            
        except Exception as e:
            raise UserError(_("Error importing Excel file: %s") % str(e))
    
    def _map_csv_to_tender(self, row):
        """Map CSV columns to tender fields"""
        # Define field mappings
        field_mappings = {
            'Reference Number': 'name',
            'Title': 'title',
            'Description': 'description',
            'Submission Date': 'submission_date',
            'Publication Date': 'publication_date',
            'Opening Date': 'opening_date',
            'Estimated Value': 'tender_value',
            'Bid Security': 'bid_security',
            'EMD Required': 'emd_required',
            'EMD Amount': 'emd_amount',
            'Issuing Authority': 'issuing_authority',
            'Source URL': 'source_url',
            'Tender Type': 'tender_type',
            'GEM Bid ID': 'gem_bid_id'
        }
        
        # Create tender data dictionary
        tender_data = {
            'company_id': self.company_id.id,
            'department_id': self.department_id.id if self.department_id else False,
            'user_id': self.user_id.id
        }
        
        # Map CSV columns to tender fields
        for csv_key, field in field_mappings.items():
            if csv_key in row and row[csv_key]:
                # Handle special cases
                if field == 'submission_date' and row[csv_key]:
                    try:
                        tender_data[field] = fields.Datetime.to_datetime(row[csv_key])
                    except:
                        pass
                elif field == 'publication_date' and row[csv_key]:
                    try:
                        tender_data[field] = fields.Datetime.to_datetime(row[csv_key])
                    except:
                        pass
                elif field == 'opening_date' and row[csv_key]:
                    try:
                        tender_data[field] = fields.Datetime.to_datetime(row[csv_key])
                    except:
                        pass
                elif field == 'emd_required' and row[csv_key]:
                    tender_data[field] = row[csv_key].lower() in ['yes', 'true', '1']
                elif field == 'tender_type' and row[csv_key]:
                    # Map string to selection value
                    type_map = {
                        'Open': 'open',
                        'Limited': 'limited',
                        'Single': 'single',
                        'Global': 'global',
                        'GeM': 'gem'
                    }
                    tender_data[field] = type_map.get(row[csv_key], 'open')
                else:
                    tender_data[field] = row[csv_key]
        
        return tender_data
    
    def _map_excel_to_tender(self, row):
        """Map Excel columns to tender fields"""
        # Use the same mapping as CSV
        return self._map_csv_to_tender(row)
    
    def _create_update_tender(self, tender_data):
        """Create or update tender based on data"""
        Tender = self.env['tender.tender']
        
        # Check if tender exists by name
        existing_tender = False
        if 'name' in tender_data and tender_data['name']:
            existing_tender = Tender.search([
                ('name', '=', tender_data['name']),
                ('company_id', '=', self.company_id.id)
            ], limit=1)
        
        # Create or update tender
        if existing_tender:
            existing_tender.write(tender_data)
            return 'updated'
        else:
            # Set default state for new tenders
            tender_data['state'] = 'draft'
            Tender.create(tender_data)
            return 'created'
    
    def _import_from_gem(self):
        """Import tenders from GeM Portal"""
        if not self.gem_portal_id:
            raise UserError(_("Please select a GeM Portal to import from"))
        
        log = []
        created_count = 0
        updated_count = 0
        error_count = 0
        
        try:
            # Prepare date range for import
            date_filter = {}
            if self.start_date:
                date_filter['from_date'] = self.start_date
            if self.end_date:
                date_filter['to_date'] = self.end_date
            
            # Import tenders from GeM Portal
            result = self.gem_portal_id._import_tenders(
                import_all=self.import_all,
                date_filter=date_filter,
                department_id=self.department_id.id if self.department_id else False,
                user_id=self.user_id.id
            )
            
            created_count = result.get('created', 0)
            updated_count = result.get('updated', 0)
            error_count = result.get('errors', 0)
            
            # Summary log
            log.append(_("Import Summary:"))
            log.append(_("Tenders created: %s") % created_count)
            log.append(_("Tenders updated: %s") % updated_count)
            log.append(_("Errors: %s") % error_count)
            
            if 'error_details' in result and result['error_details']:
                log.append(_("\nError Details:"))
                for error in result['error_details']:
                    log.append(error)
            
            self.import_log = "\n".join(log)
            
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'tender.import.wizard',
                'view_mode': 'form',
                'res_id': self.id,
                'views': [(False, 'form')],
                'target': 'new',
            }
            
        except Exception as e:
            raise UserError(_("Error importing from GeM Portal: %s") % str(e))
    
    def _import_from_url(self):
        """Import tenders from a website URL"""
        if not self.url:
            raise UserError(_("Please enter a URL to import from"))
        
        # This method would require integration with a web scraping service
        # For demonstration purposes, we'll just return an error
        raise UserError(_("URL import is not implemented in this version. Please use file or GeM import."))


class TenderBidWizard(models.TransientModel):
    _name = 'tender.bid.wizard'
    _description = 'Create Bid'
    
    tender_id = fields.Many2one('tender.tender', string='Tender', required=True)
    name = fields.Char(string='Bid Reference', required=True, default=lambda self: self._default_name())
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user)
    
    # Bid Details
    technical_score = fields.Float(string='Technical Score')
    financial_bid = fields.Monetary(string='Financial Bid', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='tender_id.currency_id')
    notes = fields.Html(string='Notes')
    
    # Documents
    document_ids = fields.Many2many('tender.document', string='Documents to Include')
    new_document = fields.Binary(string='Upload New Document')
    new_document_name = fields.Char(string='Document Name')
    new_document_type = fields.Selection([
        ('tender_notice', 'Tender Notice'),
        ('technical_specification', 'Technical Specification'),
        ('financial_specification', 'Financial Specification'),
        ('corrigendum', 'Corrigendum'),
        ('pre_bid_query', 'Pre-bid Query'),
        ('bid_document', 'Bid Document'),
        ('submission', 'Submission Document'),
        ('other', 'Other')
    ], string='Document Type', default='bid_document')
    
    def _default_name(self):
        """Generate default bid name"""
        active_id = self.env.context.get('active_id')
        if active_id:
            tender = self.env['tender.tender'].browse(active_id)
            return f"Bid for {tender.name}" if tender else "New Bid"
        return "New Bid"
    
    @api.onchange('tender_id')
    def _onchange_tender_id(self):
        """Update document domain when tender changes"""
        if self.tender_id:
            return {'domain': {'document_ids': [('tender_id', '=', self.tender_id.id)]}}
    
    def action_create_bid(self):
        """Create a new bid"""
        self.ensure_one()
        
        # Check if tender is in valid state
        if self.tender_id.state not in ['approved', 'preparation']:
            raise UserError(_("Tenders must be in 'Approved' or 'Preparation' state to create bids."))
        
        # Create bid
        bid_vals = {
            'name': self.name,
            'tender_id': self.tender_id.id,
            'user_id': self.user_id.id,
            'technical_score': self.technical_score,
            'financial_bid': self.financial_bid,
            'notes': self.notes,
            'state': 'draft'
        }
        
        bid = self.env['tender.bid'].create(bid_vals)
        
        # Link existing documents to bid
        if self.document_ids:
            for doc in self.document_ids:
                doc.write({'bid_id': bid.id})
        
        # Create new document if uploaded
        if self.new_document:
            self.env['tender.document'].create({
                'name': self.new_document_name or 'Bid Document',
                'tender_id': self.tender_id.id,
                'bid_id': bid.id,
                'file': self.new_document,
                'file_name': self.new_document_name,
                'document_type': self.new_document_type,
                'date': fields.Date.today(),
                'user_id': self.user_id.id
            })
        
        # If tender is in approved state, move it to preparation
        if self.tender_id.state == 'approved':
            self.tender_id.action_start_preparation()
        
        # Show the created bid
        return {
            'name': _('Bid'),
            'view_mode': 'form',
            'res_model': 'tender.bid',
            'res_id': bid.id,
            'type': 'ir.actions.act_window'
        }
