# models/analytics_team.py
import logging
from datetime import datetime, timedelta
import json
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class TenderTeam(models.Model):
    _name = 'tender.team'
    _description = 'Tender Team'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Team Name', required=True, tracking=True)
    description = fields.Text(string='Description')
    
    # Team Members
    leader_id = fields.Many2one('res.users', string='Team Leader', required=True, tracking=True)
    member_ids = fields.One2many('tender.team.member', 'team_id', string='Team Members')
    
    # Related Information
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    department_id = fields.Many2one('tender.department', string='Department')
    
    # Specialization
    specialization_ids = fields.Many2many('tender.category', string='Specializations')
    
    # Activity Tracking
    active = fields.Boolean(default=True)
    creation_date = fields.Date(string='Creation Date', default=fields.Date.today)
    
    # Statistics
    tender_count = fields.Integer(compute='_compute_tender_count')
    active_tender_count = fields.Integer(compute='_compute_active_tender_count')
    success_rate = fields.Float(compute='_compute_success_rate', string='Success Rate (%)')
    
    # Notes
    notes = fields.Html(string='Notes')
    
    @api.depends('tender_ids')
    def _compute_tender_count(self):
        for team in self:
            team.tender_count = self.env['tender.tender'].search_count([
                ('team_id', '=', team.id)
            ])
    
    @api.depends('tender_ids', 'tender_ids.state')
    def _compute_active_tender_count(self):
        for team in self:
            team.active_tender_count = self.env['tender.tender'].search_count([
                ('team_id', '=', team.id),
                ('state', 'not in', ['awarded', 'rejected', 'canceled'])
            ])
    
    @api.depends('tender_ids', 'tender_ids.state')
    def _compute_success_rate(self):
        for team in self:
            tenders = self.env['tender.tender'].search([
                ('team_id', '=', team.id),
                ('state', 'in', ['awarded', 'rejected'])
            ])
            
            if not tenders:
                team.success_rate = 0.0
                continue
            
            awarded = len(tenders.filtered(lambda t: t.state == 'awarded'))
            total = len(tenders)
            
            team.success_rate = (awarded / total) * 100 if total > 0 else 0.0
    
    def action_view_tenders(self):
        """View tenders for this team"""
        self.ensure_one()
        return {
            'name': _('Tenders'),
            'view_mode': 'tree,form',
            'res_model': 'tender.tender',
            'domain': [('team_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_team_id': self.id}
        }
    
    def action_view_active_tenders(self):
        """View active tenders for this team"""
        self.ensure_one()
        return {
            'name': _('Active Tenders'),
            'view_mode': 'tree,form',
            'res_model': 'tender.tender',
            'domain': [
                ('team_id', '=', self.id),
                ('state', 'not in', ['awarded', 'rejected', 'canceled'])
            ],
            'type': 'ir.actions.act_window',
            'context': {'default_team_id': self.id}
        }
    
    def action_send_team_report(self):
        """Send team performance report to team leader"""
        template = self.env.ref('tender_management.email_template_team_performance_report')
        for team in self:
            template.send_mail(team.id, force_send=True)


class TenderTeamMember(models.Model):
    _name = 'tender.team.member'
    _description = 'Tender Team Member'
    
    name = fields.Char(string='Name', related='user_id.name', store=True)
    team_id = fields.Many2one('tender.team', string='Team', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', string='User', required=True)
    
    # Role
    role = fields.Selection([
        ('technical', 'Technical Expert'),
        ('financial', 'Financial Expert'),
        ('legal', 'Legal Expert'),
        ('coordinator', 'Coordinator'),
        ('approver', 'Approver'),
        ('other', 'Other')
    ], string='Role', default='other', required=True)
    
    role_description = fields.Text(string='Role Description')
    
    # Contact Information
    email = fields.Char(string='Email', related='user_id.email', readonly=True)
    phone = fields.Char(string='Phone')
    
    # Workload
    tender_ids = fields.Many2many('tender.tender', string='Assigned Tenders', compute='_compute_assigned_tenders')
    active_tender_count = fields.Integer(compute='_compute_active_tender_count')
    workload = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('overloaded', 'Overloaded')
    ], string='Workload', compute='_compute_workload', store=True)
    
    # Skills
    skill_ids = fields.Many2many('tender.skill', string='Skills')
    
    _sql_constraints = [
        ('user_team_uniq', 'unique(user_id, team_id)', 'This user is already a member of this team!')
    ]
    
    @api.depends('user_id', 'team_id', 'team_id.tender_ids')
    def _compute_assigned_tenders(self):
        for member in self:
            # Find tenders where this team member is a responsible
            tenders = self.env['tender.tender'].search([
                '|',
                ('team_id', '=', member.team_id.id),
                ('user_id', '=', member.user_id.id)
            ])
            member.tender_ids = [(6, 0, tenders.ids)]
    
    @api.depends('tender_ids', 'tender_ids.state')
    def _compute_active_tender_count(self):
        for member in self:
            member.active_tender_count = len(member.tender_ids.filtered(
                lambda t: t.state not in ['awarded', 'rejected', 'canceled']
            ))
    
    @api.depends('active_tender_count')
    def _compute_workload(self):
        for member in self:
            active_count = member.active_tender_count
            if active_count <= 2:
                member.workload = 'low'
            elif active_count <= 5:
                member.workload = 'medium'
            elif active_count <= 8:
                member.workload = 'high'
            else:
                member.workload = 'overloaded'


class TenderSkill(models.Model):
    _name = 'tender.skill'
    _description = 'Tender Skill'
    
    name = fields.Char(string='Skill Name', required=True)
    description = fields.Text(string='Description')
    
    # Categories
    category = fields.Selection([
        ('technical', 'Technical'),
        ('financial', 'Financial'),
        ('legal', 'Legal'),
        ('management', 'Management'),
        ('other', 'Other')
    ], string='Category', default='other', required=True)
    
    # Statistics
    member_count = fields.Integer(compute='_compute_member_count')
    
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'This skill already exists!')
    ]
    
    @api.depends('member_ids')
    def _compute_member_count(self):
        for skill in self:
            skill.member_count = self.env['tender.team.member'].search_count([
                ('skill_ids', 'in', skill.id)
            ])


class TenderAnalytics(models.Model):
    _name = 'tender.analytics'
    _description = 'Tender Analytics'
    
    name = fields.Char(string='Reference', compute='_compute_name')
    tender_id = fields.Many2one('tender.tender', string='Tender', required=True, ondelete='cascade')
    date = fields.Date(string='Date', default=fields.Date.today, required=True)
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user)
    
    # Analytics Data
    state = fields.Selection(related='tender_id.state', string='Tender Status')
    tender_type = fields.Selection(related='tender_id.tender_type', string='Tender Type')
    tender_value = fields.Monetary(related='tender_id.tender_value', string='Tender Value')
    currency_id = fields.Many2one(related='tender_id.currency_id')
    
    # Timeline
    preparation_time = fields.Integer(string='Preparation Time (Days)', compute='_compute_times', store=True)
    response_time = fields.Integer(string='Response Time (Days)', compute='_compute_times', store=True)
    
    # Success Metrics
    is_successful = fields.Boolean(string='Is Successful', compute='_compute_success_metrics', store=True)
    win_probability = fields.Float(string='Win Probability (%)', default=50.0)
    competing_bids = fields.Integer(string='Competing Bids')
    
    # Cost Analysis
    preparation_cost = fields.Monetary(string='Preparation Cost', currency_field='currency_id')
    submission_cost = fields.Monetary(string='Submission Cost', currency_field='currency_id')
    total_cost = fields.Monetary(string='Total Cost', compute='_compute_total_cost', store=True, currency_field='currency_id')
    roi_if_won = fields.Float(string='ROI if Won (%)', compute='_compute_roi', store=True)
    
    # Data for Charts
    data_json = fields.Text(string='Analytics Data JSON', compute='_compute_data_json')
    
    @api.depends('tender_id')
    def _compute_name(self):
        for record in self:
            record.name = _('Analytics for %s') % record.tender_id.name if record.tender_id else _('New Analytics')
    
    @api.depends('tender_id.state', 'tender_id.submission_date', 'date')
    def _compute_times(self):
        for record in self:
            if not record.tender_id:
                record.preparation_time = 0
                record.response_time = 0
                continue
            
            # Calculate preparation time
            if record.tender_id.submission_date and record.tender_id.publication_date:
                delta = record.tender_id.submission_date - record.tender_id.publication_date
                record.preparation_time = delta.days
            else:
                record.preparation_time = 0
            
            # Calculate response time based on state transitions
            activity_logs = self.env['mail.message'].search([
                ('model', '=', 'tender.tender'),
                ('res_id', '=', record.tender_id.id),
                ('tracking_value_ids', '!=', False)
            ], order='create_date asc')
            
            submission_date = None
            approval_date = None
            
            for log in activity_logs:
                for value in log.tracking_value_ids:
                    if value.field_desc == 'Status':
                        if value.new_value_char == 'Approved to Bid':
                            approval_date = log.create_date
                        elif value.new_value_char == 'Bid Submitted':
                            submission_date = log.create_date
            
            if submission_date and approval_date:
                delta = submission_date - approval_date
                record.response_time = delta.days
            else:
                record.response_time = 0
    
    @api.depends('tender_id.state')
    def _compute_success_metrics(self):
        for record in self:
            record.is_successful = record.tender_id.state == 'awarded' if record.tender_id else False
    
    @api.depends('preparation_cost', 'submission_cost')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = (record.preparation_cost or 0.0) + (record.submission_cost or 0.0)
    
    @api.depends('total_cost', 'tender_id.tender_value')
    def _compute_roi(self):
        for record in self:
            if record.total_cost and record.total_cost > 0 and record.tender_id.tender_value:
                profit = record.tender_id.tender_value - record.total_cost
                record.roi_if_won = (profit / record.total_cost) * 100
            else:
                record.roi_if_won = 0.0
    
    def _compute_data_json(self):
        """Compute JSON data for charts and analytics"""
        for record in self:
            data = {
                'tender_name': record.tender_id.name if record.tender_id else '',
                'tender_value': record.tender_value,
                'preparation_time': record.preparation_time,
                'response_time': record.response_time,
                'win_probability': record.win_probability,
                'is_successful': record.is_successful,
                'competing_bids': record.competing_bids,
                'preparation_cost': record.preparation_cost,
                'submission_cost': record.submission_cost,
                'total_cost': record.total_cost,
                'roi_if_won': record.roi_if_won
            }
            
            # Get timeline data
            timeline_data = self._get_timeline_data()
            data['timeline'] = timeline_data
            
            # Get cost breakdown
            cost_data = self._get_cost_data()
            data['costs'] = cost_data
            
            record.data_json = json.dumps(data)
    
    def _get_timeline_data(self):
        """Get timeline data for the tender"""
        self.ensure_one()
        if not self.tender_id:
            return []
        
        timeline = []
        
        # Add state changes
        state_changes = self.env['mail.message'].search([
            ('model', '=', 'tender.tender'),
            ('res_id', '=', self.tender_id.id),
            ('tracking_value_ids.field_desc', '=', 'Status')
        ], order='create_date asc')
        
        for message in state_changes:
            for value in message.tracking_value_ids:
                if value.field_desc == 'Status':
                    timeline.append({
                        'date': message.create_date.strftime('%Y-%m-%d'),
                        'event': f"Status changed from '{value.old_value_char}' to '{value.new_value_char}'",
                        'user': message.author_id.name
                    })
        
        # Add key dates
        date_fields = [
            ('publication_date', 'Publication Date'),
            ('submission_date', 'Submission Deadline'),
            ('opening_date', 'Opening Date'),
            ('clarification_date', 'Clarification Deadline')
        ]
        
        for field, label in date_fields:
            value = getattr(self.tender_id, field)
            if value:
                timeline.append({
                    'date': value.strftime('%Y-%m-%d'),
                    'event': label,
                    'user': ''
                })
        
        return sorted(timeline, key=lambda x: x['date'])
    
    def _get_cost_data(self):
        """Get cost breakdown data"""
        self.ensure_one()
        
        return {
            'preparation': self.preparation_cost or 0.0,
            'submission': self.submission_cost or 0.0,
            'total': self.total_cost or 0.0
        }
    
    @api.model
    def get_success_rate_by_department(self):
        """Get success rate by department"""
        departments = self.env['tender.department'].search([])
        result = []
        
        for dept in departments:
            tenders = self.env['tender.tender'].search([
                ('department_id', '=', dept.id),
                ('state', 'in', ['awarded', 'rejected'])
            ])
            
            if not tenders:
                continue
            
            awarded = len(tenders.filtered(lambda t: t.state == 'awarded'))
            total = len(tenders)
            
            success_rate = (awarded / total) * 100 if total > 0 else 0
            
            result.append({
                'department': dept.name,
                'success_rate': success_rate,
                'awarded': awarded,
                'total': total
            })
            
        return result
    
    @api.model
    def get_tender_value_by_type(self):
        """Get tender value by type"""
        tender_types = dict(self.env['tender.tender']._fields['tender_type'].selection)
        result = []
        
        for type_code, type_name in tender_types.items():
            tenders = self.env['tender.tender'].search([
                ('tender_type', '=', type_code),
                ('state', '=', 'awarded')
            ])
            
            total_value = sum(tenders.mapped('tender_value'))
            count = len(tenders)
            
            result.append({
                'type': type_name,
                'value': total_value,
                'count': count
            })
            
        return result
    
    @api.model
    def get_preparation_time_stats(self):
        """Get statistics for tender preparation time"""
        analytics = self.search([])
        
        if not analytics:
            return {
                'average': 0,
                'min': 0,
                'max': 0,
                'distribution': []
            }
        
        preparation_times = analytics.mapped('preparation_time')
        
        result = {
            'average': sum(preparation_times) / len(preparation_times) if preparation_times else 0,
            'min': min(preparation_times) if preparation_times else 0,
            'max': max(preparation_times) if preparation_times else 0,
            'distribution': []
        }
        
        # Create distribution for ranges
        ranges = [
            (0, 7, '0-7 days'),
            (8, 14, '8-14 days'),
            (15, 30, '15-30 days'),
            (31, 60, '31-60 days'),
            (61, float('inf'), '60+ days')
        ]
        
        for start, end, label in ranges:
            count = len([t for t in preparation_times if start <= t <= end])
            result['distribution'].append({
                'range': label,
                'count': count
            })
        
        return result
