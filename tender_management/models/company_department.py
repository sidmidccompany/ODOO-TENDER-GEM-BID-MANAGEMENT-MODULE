# models/company_department.py
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class TenderCompany(models.Model):
    _name = 'tender.company'
    _description = 'Tender Company Profile'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Profile Name', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    # Company Details
    legal_name = fields.Char(string='Legal Name', tracking=True)
    registration_number = fields.Char(string='Registration Number', tracking=True)
    tax_id = fields.Char(string='Tax ID', tracking=True)
    establishment_year = fields.Char(string='Year of Establishment', tracking=True)
    
    # Address
    street = fields.Char(string='Street', tracking=True)
    street2 = fields.Char(string='Street2', tracking=True)
    city = fields.Char(string='City', tracking=True)
    state_id = fields.Many2one('res.country.state', string='State', tracking=True)
    zip = fields.Char(string='ZIP', tracking=True)
    country_id = fields.Many2one('res.country', string='Country', tracking=True)
    
    # Contact
    phone = fields.Char(string='Phone', tracking=True)
    email = fields.Char(string='Email', tracking=True)
    website = fields.Char(string='Website', tracking=True)
    
    # Financial Information
    annual_turnover = fields.Monetary(string='Annual Turnover', currency_field='currency_id', tracking=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    net_worth = fields.Monetary(string='Net Worth', currency_field='currency_id', tracking=True)
    
    # Certifications and Eligibility
    certification_ids = fields.One2many('tender.company.certification', 'company_id', string='Certifications')
    eligibility_criteria_ids = fields.One2many('tender.company.eligibility', 'company_id', string='Eligibility Criteria')
    
    # Documents
    document_ids = fields.One2many('tender.company.document', 'company_id', string='Documents')
    
    # GeM Registration
    is_registered_gem = fields.Boolean(string='Registered on GeM', default=False, tracking=True)
    gem_registration_id = fields.Char(string='GeM Registration ID', tracking=True)
    gem_registration_date = fields.Date(string='GeM Registration Date', tracking=True)
    
    # Bank Details
    bank_name = fields.Char(string='Bank Name', tracking=True)
    bank_account_number = fields.Char(string='Bank Account Number', tracking=True)
    bank_branch = fields.Char(string='Bank Branch', tracking=True)
    bank_ifsc = fields.Char(string='IFSC Code', tracking=True)
    
    # Notes
    notes = fields.Html(string='Notes')
    
    # Statistics
    tender_count = fields.Integer(compute='_compute_tender_count')
    department_count = fields.Integer(compute='_compute_department_count')
    
    @api.depends('tender_ids')
    def _compute_tender_count(self):
        for company in self:
            company.tender_count = self.env['tender.tender'].search_count([
                ('company_id', '=', company.company_id.id)
            ])
    
    @api.depends('department_ids')
    def _compute_department_count(self):
        for company in self:
            company.department_count = self.env['tender.department'].search_count([
                ('company_id', '=', company.company_id.id)
            ])
    
    def action_view_tenders(self):
        """View tenders for this company"""
        self.ensure_one()
        return {
            'name': _('Tenders'),
            'view_mode': 'tree,form',
            'res_model': 'tender.tender',
            'domain': [('company_id', '=', self.company_id.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_company_id': self.company_id.id}
        }
    
    def action_view_departments(self):
        """View departments for this company"""
        self.ensure_one()
        return {
            'name': _('Departments'),
            'view_mode': 'tree,form',
            'res_model': 'tender.department',
            'domain': [('company_id', '=', self.company_id.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_company_id': self.company_id.id}
        }


class TenderCompanyCertification(models.Model):
    _name = 'tender.company.certification'
    _description = 'Company Certification'
    
    name = fields.Char(string='Certification Name', required=True)
    company_id = fields.Many2one('tender.company', string='Company', required=True, ondelete='cascade')
    certification_number = fields.Char(string='Certification Number')
    issuing_authority = fields.Char(string='Issuing Authority')
    issue_date = fields.Date(string='Issue Date')
    expiry_date = fields.Date(string='Expiry Date')
    document = fields.Binary(string='Certificate Document', attachment=True)
    document_name = fields.Char(string='Document Name')
    notes = fields.Text(string='Notes')
    
    @api.constrains('issue_date', 'expiry_date')
    def _check_dates(self):
        for record in self:
            if record.issue_date and record.expiry_date and record.issue_date > record.expiry_date:
                raise ValidationError(_("Issue Date cannot be later than Expiry Date"))


class TenderCompanyEligibility(models.Model):
    _name = 'tender.company.eligibility'
    _description = 'Company Eligibility Criteria'
    
    name = fields.Char(string='Eligibility Criteria', required=True)
    company_id = fields.Many2one('tender.company', string='Company', required=True, ondelete='cascade')
    value = fields.Char(string='Value')
    document = fields.Binary(string='Supporting Document', attachment=True)
    document_name = fields.Char(string='Document Name')
    notes = fields.Text(string='Notes')


class TenderCompanyDocument(models.Model):
    _name = 'tender.company.document'
    _description = 'Company Document'
    
    name = fields.Char(string='Document Name', required=True)
    company_id = fields.Many2one('tender.company', string='Company', required=True, ondelete='cascade')
    document_type = fields.Selection([
        ('registration', 'Company Registration'),
        ('tax', 'Tax Document'),
        ('financial', 'Financial Document'),
        ('technical', 'Technical Document'),
        ('quality', 'Quality Document'),
        ('legal', 'Legal Document'),
        ('other', 'Other')
    ], string='Document Type', default='other', required=True)
    file = fields.Binary(string='File', attachment=True, required=True)
    file_name = fields.Char(string='File Name')
    issue_date = fields.Date(string='Issue Date')
    expiry_date = fields.Date(string='Expiry Date')
    is_valid = fields.Boolean(string='Is Valid', compute='_compute_is_valid', store=True)
    notes = fields.Text(string='Notes')
    
    @api.depends('expiry_date')
    def _compute_is_valid(self):
        today = fields.Date.today()
        for record in self:
            record.is_valid = not record.expiry_date or record.expiry_date >= today
    
    @api.constrains('issue_date', 'expiry_date')
    def _check_dates(self):
        for record in self:
            if record.issue_date and record.expiry_date and record.issue_date > record.expiry_date:
                raise ValidationError(_("Issue Date cannot be later than Expiry Date"))


class TenderDepartment(models.Model):
    _name = 'tender.department'
    _description = 'Tender Department'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Department Name', required=True, tracking=True)
    code = fields.Char(string='Department Code', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    
    # Manager
    manager_id = fields.Many2one('res.users', string='Manager', tracking=True)
    
    # Team
    member_ids = fields.Many2many('res.users', string='Members')
    
    # Address
    address = fields.Text(string='Address', tracking=True)
    
    # Contact
    phone = fields.Char(string='Phone', tracking=True)
    email = fields.Char(string='Email', tracking=True)
    
    # Tender Categories
    category_ids = fields.Many2many('tender.category', string='Tender Categories')
    
    # Budget
    annual_budget = fields.Monetary(string='Annual Budget', currency_field='currency_id', tracking=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    budget_utilized = fields.Monetary(string='Budget Utilized', currency_field='currency_id', compute='_compute_budget_utilized')
    budget_remaining = fields.Monetary(string='Budget Remaining', currency_field='currency_id', compute='_compute_budget_remaining')
    
    # Statistics
    tender_count = fields.Integer(compute='_compute_tender_count')
    active_tender_count = fields.Integer(compute='_compute_active_tender_count')
    
    # Notes
    notes = fields.Html(string='Notes')
    
    @api.depends('tender_ids', 'tender_ids.tender_value')
    def _compute_budget_utilized(self):
        for department in self:
            awarded_tenders = self.env['tender.tender'].search([
                ('department_id', '=', department.id),
                ('state', '=', 'awarded'),
            ])
            department.budget_utilized = sum(tender.tender_value for tender in awarded_tenders)
    
    @api.depends('annual_budget', 'budget_utilized')
    def _compute_budget_remaining(self):
        for department in self:
            department.budget_remaining = department.annual_budget - department.budget_utilized
    
    @api.depends('tender_ids')
    def _compute_tender_count(self):
        for department in self:
            department.tender_count = self.env['tender.tender'].search_count([
                ('department_id', '=', department.id)
            ])
    
    @api.depends('tender_ids', 'tender_ids.state')
    def _compute_active_tender_count(self):
        for department in self:
            department.active_tender_count = self.env['tender.tender'].search_count([
                ('department_id', '=', department.id),
                ('state', 'not in', ['awarded', 'rejected', 'canceled'])
            ])
    
    def action_view_tenders(self):
        """View tenders for this department"""
        self.ensure_one()
        return {
            'name': _('Tenders'),
            'view_mode': 'tree,form',
            'res_model': 'tender.tender',
            'domain': [('department_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_department_id': self.id}
        }
    
    def action_view_active_tenders(self):
        """View active tenders for this department"""
        self.ensure_one()
        return {
            'name': _('Active Tenders'),
            'view_mode': 'tree,form',
            'res_model': 'tender.tender',
            'domain': [
                ('department_id', '=', self.id),
                ('state', 'not in', ['awarded', 'rejected', 'canceled'])
            ],
            'type': 'ir.actions.act_window',
            'context': {'default_department_id': self.id}
        }


class TenderCategory(models.Model):
    _name = 'tender.category'
    _description = 'Tender Category'
    
    name = fields.Char(string='Category Name', required=True)
    code = fields.Char(string='Category Code')
    parent_id = fields.Many2one('tender.category', string='Parent Category')
    child_ids = fields.One2many('tender.category', 'parent_id', string='Child Categories')
    description = fields.Text(string='Description')
    
    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Category name already exists!"),
    ]
    
    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('Error! You cannot create recursive categories.'))
    
    def name_get(self):
        result = []
        for category in self:
            name = category.name
            if category.parent_id:
                name = f"{category.parent_id.name} / {name}"
            result.append((category.id, name))
        return result


class ResUsers(models.Model):
    _inherit = 'res.users'
    
    department_ids = fields.Many2many('tender.department', string='Tender Departments')
    is_tender_user = fields.Boolean(string='Is Tender User', compute='_compute_is_tender_user', store=True)
    
    @api.depends('groups_id')
    def _compute_is_tender_user(self):
        tender_group = self.env.ref('tender_management.group_tender_user', False)
        for user in self:
            user.is_tender_user = tender_group.id in user.groups_id.ids if tender_group else False
