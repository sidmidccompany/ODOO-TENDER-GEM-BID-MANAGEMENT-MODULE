# models/tender.py
import logging
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class TenderTender(models.Model):
    _name = 'tender.tender'
    _description = 'Tender Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Tender Reference', required=True, copy=False, readonly=True, 
                       states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    title = fields.Char(string='Tender Title', required=True, tracking=True)
    description = fields.Html(string='Description', tracking=True)
    
    # Organization Details
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    department_id = fields.Many2one('tender.department', string='Department', tracking=True)
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user, tracking=True)
    
    # Dates
    submission_date = fields.Datetime(string='Submission Deadline', required=True, tracking=True)
    publication_date = fields.Datetime(string='Publication Date', tracking=True)
    opening_date = fields.Datetime(string='Opening Date', tracking=True)
    clarification_date = fields.Datetime(string='Clarification Deadline', tracking=True)
    
    # Financial Information
    tender_value = fields.Monetary(string='Estimated Value', currency_field='currency_id', tracking=True)
    bid_security = fields.Monetary(string='Bid Security Amount', currency_field='currency_id', tracking=True)
    emd_required = fields.Boolean(string='EMD Required', default=False, tracking=True)
    emd_amount = fields.Monetary(string='EMD Amount', currency_field='currency_id', tracking=True)
    
    # Source Information
    issuing_authority = fields.Char(string='Issuing Authority', tracking=True)
    source_url = fields.Char(string='Source URL', tracking=True)
    tender_type = fields.Selection([
        ('open', 'Open Tender'),
        ('limited', 'Limited Tender'),
        ('single', 'Single Tender'),
        ('global', 'Global Tender'),
        ('gem', 'GeM Tender')
    ], string='Tender Type', default='open', required=True, tracking=True)
    gem_portal_id = fields.Many2one('gem.portal', string='GeM Portal', tracking=True)
    gem_bid_id = fields.Char(string='GeM Bid Number', tracking=True)
    
    # State Management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('approved', 'Approved to Bid'),
        ('preparation', 'Bid Preparation'),
        ('submitted', 'Bid Submitted'),
        ('awarded', 'Awarded'),
        ('rejected', 'Rejected'),
        ('canceled', 'Canceled')
    ], string='Status', default='draft', tracking=True, group_expand='_expand_states')
    
    # Related Documents and Bids
    document_ids = fields.One2many('tender.document', 'tender_id', string='Documents')
    bid_ids = fields.One2many('tender.bid', 'tender_id', string='Bids')
    active_bid_id = fields.Many2one('tender.bid', string='Active Bid', compute='_compute_active_bid')
    
    # Team and Analytics
    team_id = fields.Many2one('tender.team', string='Responsible Team', tracking=True)
    team_member_ids = fields.Many2many('res.users', string='Team Members', compute='_compute_team_members')
    analytics_id = fields.Many2one('tender.analytics', string='Analytics')
    
    # Additional Fields
    tags = fields.Many2many('tender.tag', string='Tags')
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
        ('3', 'Very High')
    ], string='Priority', default='1', tracking=True)
    color = fields.Integer(string='Color Index')
    deadline_reminder = fields.Boolean(string='Deadline Reminder', default=True)
    is_favorite = fields.Boolean(string='Favorite')
    
    # Technical Fields
    has_submission_deadline_passed = fields.Boolean(compute='_compute_deadlines', search='_search_deadline_passed')
    days_to_deadline = fields.Integer(compute='_compute_deadlines')
    document_count = fields.Integer(compute='_compute_document_count')
    bid_count = fields.Integer(compute='_compute_bid_count')
    
    # Smart Buttons
    def _compute_document_count(self):
        for tender in self:
            tender.document_count = len(tender.document_ids)
    
    def _compute_bid_count(self):
        for tender in self:
            tender.bid_count = len(tender.bid_ids)
    
    @api.depends('bid_ids', 'bid_ids.state')
    def _compute_active_bid(self):
        for tender in self:
            active_bids = tender.bid_ids.filtered(lambda b: b.state in ['draft', 'review', 'approved'])
            tender.active_bid_id = active_bids[0] if active_bids else False
    
    @api.depends('team_id', 'team_id.member_ids')
    def _compute_team_members(self):
        for tender in self:
            tender.team_member_ids = tender.team_id.member_ids.mapped('user_id') if tender.team_id else False
    
    @api.depends('submission_date')
    def _compute_deadlines(self):
        now = fields.Datetime.now()
        for tender in self:
            if tender.submission_date:
                tender.has_submission_deadline_passed = tender.submission_date < now
                delta = tender.submission_date - now
                tender.days_to_deadline = delta.days if delta.days > 0 else 0
            else:
                tender.has_submission_deadline_passed = False
                tender.days_to_deadline = 0
    
    def _search_deadline_passed(self, operator, value):
        now = fields.Datetime.now()
        if operator == '=' and value:
            return [('submission_date', '<', now)]
        elif operator == '=' and not value:
            return [('submission_date', '>=', now)]
        elif operator == '!=' and value:
            return [('submission_date', '>=', now)]
        elif operator == '!=' and not value:
            return [('submission_date', '<', now)]
        return []
    
    def _expand_states(self, states, domain, order):
        return [key for key, val in self._fields['state'].selection]
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('tender.tender') or _('New')
        return super(TenderTender, self).create(vals_list)
    
    def write(self, vals):
        # Automatically create an analytics record if state changes
        if vals.get('state') and not self.analytics_id:
            self._create_analytics_record()
        return super(TenderTender, self).write(vals)
    
    def _create_analytics_record(self):
        """Create analytics record for tracking tender metrics"""
        for tender in self:
            self.env['tender.analytics'].create({
                'tender_id': tender.id,
                'date': fields.Date.today(),
                'user_id': self.env.user.id,
            })
    
    def action_submit_for_review(self):
        """Submit the tender for internal review"""
        for tender in self:
            if tender.state != 'draft':
                raise UserError(_("Only draft tenders can be submitted for review."))
            tender.write({'state': 'review'})
            # Notify team members
            tender._notify_team_members(
                message_subject=_("Tender Submitted for Review"),
                message_body=_(f"The tender {tender.name} has been submitted for review.")
            )
    
    def action_approve(self):
        """Approve the tender for bidding"""
        for tender in self:
            if tender.state != 'review':
                raise UserError(_("Only tenders under review can be approved."))
            tender.write({'state': 'approved'})
            # Create initial bid
            self.env['tender.bid'].create({
                'tender_id': tender.id,
                'name': f"Bid for {tender.name}",
                'user_id': self.env.user.id,
            })
    
    def action_start_preparation(self):
        """Start bid preparation process"""
        for tender in self:
            if tender.state != 'approved':
                raise UserError(_("Only approved tenders can move to bid preparation."))
            tender.write({'state': 'preparation'})
    
    def action_submit_bid(self):
        """Mark the tender as bid submitted"""
        for tender in self:
            if tender.state != 'preparation':
                raise UserError(_("Only tenders in preparation can be submitted."))
            if not tender.active_bid_id:
                raise UserError(_("No active bid found for this tender."))
            tender.write({'state': 'submitted'})
            tender.active_bid_id.write({'state': 'submitted', 'submission_date': fields.Datetime.now()})
    
    def action_mark_awarded(self):
        """Mark the tender as awarded"""
        for tender in self:
            if tender.state != 'submitted':
                raise UserError(_("Only submitted tenders can be marked as awarded."))
            tender.write({'state': 'awarded'})
            tender.active_bid_id.write({'state': 'awarded'})
    
    def action_mark_rejected(self):
        """Mark the tender as rejected"""
        for tender in self:
            if tender.state != 'submitted':
                raise UserError(_("Only submitted tenders can be marked as rejected."))
            tender.write({'state': 'rejected'})
            tender.active_bid_id.write({'state': 'rejected'})
    
    def action_cancel(self):
        """Cancel the tender"""
        for tender in self:
            if tender.state in ['awarded', 'rejected', 'canceled']:
                raise UserError(_("This tender cannot be canceled in its current state."))
            tender.write({'state': 'canceled'})
    
    def action_view_documents(self):
        """Open the documents view"""
        self.ensure_one()
        return {
            'name': _('Documents'),
            'view_mode': 'tree,form',
            'res_model': 'tender.document',
            'domain': [('tender_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_tender_id': self.id}
        }
    
    def action_view_bids(self):
        """Open the bids view"""
        self.ensure_one()
        return {
            'name': _('Bids'),
            'view_mode': 'tree,form',
            'res_model': 'tender.bid',
            'domain': [('tender_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_tender_id': self.id}
        }
    
    def action_import_from_gem(self):
        """Import tender details from GeM portal"""
        self.ensure_one()
        if not self.gem_bid_id or not self.gem_portal_id:
            raise UserError(_("GeM Bid ID and GeM Portal must be set to import from GeM."))
        # Call the external method to fetch details
        try:
            self.env['gem.portal'].fetch_tender_details(self)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Tender details successfully imported from GeM Portal.'),
                    'sticky': False,
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': str(e),
                    'sticky': False,
                    'type': 'danger'
                }
            }
    
    def action_send_deadline_reminder(self):
        """Send deadline reminder to team members"""
        template = self.env.ref('tender_management.email_template_tender_deadline_reminder')
        for tender in self:
            if tender.team_member_ids and tender.submission_date:
                template.send_mail(tender.id, force_send=True)
    
    def _notify_team_members(self, message_subject, message_body):
        """Notify team members via the chatter"""
        for tender in self:
            tender.message_post(
                body=message_body,
                subject=message_subject,
                partner_ids=tender.team_member_ids.mapped('partner_id').ids
            )
    
    @api.model
    def _cron_deadline_reminders(self):
        """Cron job to send deadline reminders"""
        today = fields.Date.today()
        tomorrow = today + timedelta(days=1)
        week_from_now = today + timedelta(days=7)
        
        # Find tenders with deadlines coming up
        tomorrow_tenders = self.search([
            ('submission_date', '>=', fields.Datetime.to_string(fields.Datetime.now().replace(hour=0, minute=0, second=0))),
            ('submission_date', '<=', fields.Datetime.to_string((fields.Datetime.now() + timedelta(days=1)).replace(hour=23, minute=59, second=59))),
            ('state', 'in', ['approved', 'preparation']),
            ('deadline_reminder', '=', True)
        ])
        
        week_tenders = self.search([
            ('submission_date', '>=', fields.Datetime.to_string((fields.Datetime.now() + timedelta(days=6)).replace(hour=0, minute=0, second=0))),
            ('submission_date', '<=', fields.Datetime.to_string((fields.Datetime.now() + timedelta(days=7)).replace(hour=23, minute=59, second=59))),
            ('state', 'in', ['approved', 'preparation']),
            ('deadline_reminder', '=', True)
        ])
        
        # Send reminders
        tomorrow_tenders.action_send_deadline_reminder()
        week_tenders.action_send_deadline_reminder()


class TenderDocument(models.Model):
    _name = 'tender.document'
    _description = 'Tender Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Document Name', required=True)
    tender_id = fields.Many2one('tender.tender', string='Tender', required=True, ondelete='cascade')
    file = fields.Binary(string='File', attachment=True, required=True)
    file_name = fields.Char(string='File Name')
    document_type = fields.Selection([
        ('tender_notice', 'Tender Notice'),
        ('technical_specification', 'Technical Specification'),
        ('financial_specification', 'Financial Specification'),
        ('corrigendum', 'Corrigendum'),
        ('pre_bid_query', 'Pre-bid Query'),
        ('bid_document', 'Bid Document'),
        ('submission', 'Submission Document'),
        ('other', 'Other')
    ], string='Document Type', default='other', required=True)
    date = fields.Date(string='Document Date', default=fields.Date.today)
    description = fields.Text(string='Description')
    is_processed_by_ocr = fields.Boolean(string='Processed by OCR', default=False)
    ocr_result_id = fields.Many2one('tender.ocr', string='OCR Result')
    is_public = fields.Boolean(string='Public Document', help="If checked, this document will be visible on the portal")
    user_id = fields.Many2one('res.users', string='Uploaded By', default=lambda self: self.env.user)
    
    def action_process_with_ocr(self):
        """Process document with OCR"""
        for doc in self:
            if doc.is_processed_by_ocr:
                raise UserError(_("This document has already been processed with OCR."))
            
            # Create OCR record
            ocr_result = self.env['tender.ocr'].create({
                'document_id': doc.id,
                'tender_id': doc.tender_id.id,
                'state': 'draft'
            })
            
            # Start OCR processing
            ocr_result.action_process()
            
            # Update document record
            doc.write({
                'is_processed_by_ocr': True,
                'ocr_result_id': ocr_result.id
            })
            
            return {
                'name': _('OCR Result'),
                'view_mode': 'form',
                'res_model': 'tender.ocr',
                'res_id': ocr_result.id,
                'type': 'ir.actions.act_window'
            }


class TenderBid(models.Model):
    _name = 'tender.bid'
    _description = 'Tender Bid'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    
    name = fields.Char(string='Bid Reference', required=True)
    tender_id = fields.Many2one('tender.tender', string='Tender', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user)
    
    # Bid Details
    technical_score = fields.Float(string='Technical Score')
    financial_bid = fields.Monetary(string='Financial Bid', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='tender_id.currency_id')
    notes = fields.Html(string='Notes')
    
    # Dates
    creation_date = fields.Datetime(string='Creation Date', default=fields.Datetime.now)
    submission_date = fields.Datetime(string='Submission Date')
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('submitted', 'Submitted'),
        ('awarded', 'Awarded'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', tracking=True)
    
    # Related Documents
    document_ids = fields.One2many('tender.document', 'bid_id', string='Bid Documents')
    
    def action_submit_for_review(self):
        """Submit bid for internal review"""
        for bid in self:
            if bid.state != 'draft':
                raise UserError(_("Only draft bids can be submitted for review."))
            bid.write({'state': 'review'})
    
    def action_approve(self):
        """Approve bid for submission"""
        for bid in self:
            if bid.state != 'review':
                raise UserError(_("Only bids under review can be approved."))
            bid.write({'state': 'approved'})
    
    def action_submit(self):
        """Mark bid as submitted"""
        for bid in self:
            if bid.state != 'approved':
                raise UserError(_("Only approved bids can be submitted."))
            bid.write({'state': 'submitted', 'submission_date': fields.Datetime.now()})
            # Update tender status if it's not already submitted
            if bid.tender_id.state != 'submitted':
                bid.tender_id.action_submit_bid()
            
    def action_mark_awarded(self):
        """Mark bid as awarded"""
        for bid in self:
            if bid.state != 'submitted':
                raise UserError(_("Only submitted bids can be marked as awarded."))
            bid.write({'state': 'awarded'})
            # Update tender status
            if bid.tender_id.state != 'awarded':
                bid.tender_id.action_mark_awarded()
    
    def action_mark_rejected(self):
        """Mark bid as rejected"""
        for bid in self:
            if bid.state != 'submitted':
                raise UserError(_("Only submitted bids can be marked as rejected."))
            bid.write({'state': 'rejected'})
            # Update tender status
            if bid.tender_id.state != 'rejected':
                bid.tender_id.action_mark_rejected()


class TenderTag(models.Model):
    _name = 'tender.tag'
    _description = 'Tender Tag'
    
    name = fields.Char(string='Name', required=True)
    color = fields.Integer(string='Color Index')
    
    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists!"),
    ]
