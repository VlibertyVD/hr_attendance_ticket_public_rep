from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError 
import logging

_logger = logging.getLogger(__name__)

class HrAttendanceTicket(models.Model):
    _name = 'hr.attendance.ticket'
    _description = 'Attendance Adjustment Ticket'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin'] 

    def _default_employee(self):
        return self.env.user.employee_id

    name = fields.Char(
        string='Ticket Reference', 
        required=True, 
        copy=False, 
        readonly=True, 
        default='New'
    )

    employee_id = fields.Many2one(
        'hr.employee', 
        string='Employee', 
        required=True, 
        default=_default_employee,
        readonly=True,
    )
    
    reason_id = fields.Many2one(
        'hr.attendance.ticket.reason', 
        string='Reason', 
        required=True,
        readonly=True,
    )
    
    suggested_check_in = fields.Datetime(
        string='Suggested Check-In',
        readonly=True,
    )
    
    suggested_check_out = fields.Datetime(
        string='Suggested Check-Out',
        readonly=True,
    )
    
    message = fields.Text(
        string='Justification Message',
        readonly=True,
        tracking=True
    )

    attendance_id = fields.Many2one(
        'hr.attendance',
        string='Related Attendance',
        domain="[('employee_id', '=', employee_id)]",
        help="Select the attendance record you want to adjust, if applicable."
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft', required=True)

    attendance_check_in = fields.Datetime(
        related='attendance_id.check_in', 
        string='Original Check-In', 
        readonly=True
    )
    attendance_check_out = fields.Datetime(
        related='attendance_id.check_out', 
        string='Original Check-Out', 
        readonly=True
    )

    ticket_type = fields.Selection([
        ('modify', 'Modify existing attendance'),
        ('create', 'Create new attendance'),
        ('custom', 'Custom action')
    ], string='Ticket Type', required=True, tracking=True) 


    comentary = fields.Text(string='Reject Reason', tracking=True)

    validation_state = fields.Selection([
        ('valid', 'Valid'),
        ('warning', 'Warning')
    ], compute='_compute_validation', string='Validation State')
    
    validation_message = fields.Char(compute='_compute_validation', string='Validation Message')    

    original_worked_hours = fields.Float(
        string='Original Hours', 
        compute='_compute_original_worked_hours'
    )
    
    suggested_worked_hours = fields.Float(
        string='Suggested Hours', 
        compute='_compute_suggested_worked_hours'
    )

    is_officer = fields.Boolean(compute='_compute_is_officer')

    employee_user_id = fields.Many2one(related='employee_id.user_id')

    timezone_mismatch = fields.Boolean(compute='_compute_tz_mismatch')
    employee_tz_name = fields.Char(compute='_compute_tz_mismatch')
    calendar_tz_name = fields.Char(compute='_compute_tz_mismatch')


    @api.depends('employee_id', 'employee_id.tz', 'employee_id.resource_calendar_id.tz')
    def _compute_tz_mismatch(self):
        for ticket in self:

            emp_tz = ticket.employee_id.tz or self.env.user.tz

            cal_tz = ticket.employee_id.resource_calendar_id.tz

            ticket.employee_tz_name = emp_tz
            ticket.calendar_tz_name = cal_tz
            
            if emp_tz and cal_tz and emp_tz != cal_tz:
                ticket.timezone_mismatch = True
            else:
                ticket.timezone_mismatch = False

    def _compute_is_officer(self):
        for ticket in self:
            ticket.is_officer = self.env.user.has_group('hr_attendance_ticket.group_ticket_officer')

    @api.depends('attendance_check_in', 'attendance_check_out')
    def _compute_original_worked_hours(self):
        for ticket in self:
            if ticket.attendance_check_in and ticket.attendance_check_out:
                delta = ticket.attendance_check_out - ticket.attendance_check_in
                ticket.original_worked_hours = delta.total_seconds() / 3600.0
            else:
                ticket.original_worked_hours = 0.0

    @api.depends('suggested_check_in', 'suggested_check_out', 'employee_id')
    def _compute_suggested_worked_hours(self):
        for ticket in self:

            if ticket.suggested_check_in and ticket.suggested_check_out and ticket.employee_id:
                calendar = ticket.employee_id.resource_calendar_id

                if calendar:
                    hours = calendar.get_work_hours_count(
                        ticket.suggested_check_in, 
                        ticket.suggested_check_out
                    )
                    ticket.suggested_worked_hours = hours
                else:
                    delta = ticket.suggested_check_out - ticket.suggested_check_in
                    fallback_hours = delta.total_seconds() / 3600.0
                    ticket.suggested_worked_hours = fallback_hours
            else:
                ticket.suggested_worked_hours = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.attendance.ticket') or 'New'
        return super().create(vals_list)

    @api.constrains('suggested_check_in', 'suggested_check_out')
    def _check_dates(self):
        for ticket in self:
            if ticket.suggested_check_in and ticket.suggested_check_out:
                if ticket.suggested_check_in > ticket.suggested_check_out:
                    raise ValidationError("The Check-Out time cannot be earlier than the Check-In time.")

    def action_submit(self):
        for record in self:
            record.state = 'submitted'

    def action_approve(self):
        for ticket in self:
            if ticket.ticket_type == 'modify':
                if not ticket.attendance_id:
                    raise UserError("Cannot modify attendance because no original attendance record is selected.")
                
                vals = {}
                if ticket.suggested_check_in:
                    vals['check_in'] = ticket.suggested_check_in
                if ticket.suggested_check_out:
                    vals['check_out'] = ticket.suggested_check_out
                
                if vals:
                    ticket.attendance_id.write(vals)

            elif ticket.ticket_type == 'create':
                if not ticket.suggested_check_in:
                    raise UserError("To create a new attendance, 'Suggested Check-In' is required.")
                
                ticket.attendance_id = self.env['hr.attendance'].create({
                    'employee_id': ticket.employee_id.id,
                    'check_in': ticket.suggested_check_in,
                    'check_out': ticket.suggested_check_out,
                })

            elif ticket.ticket_type == 'custom':

                pass

            ticket.state = 'approved'

    def action_reject(self):
        for ticket in self:
            if not ticket.comentary:
                raise UserError("You must provide a response before rejecting the ticket.")
            ticket.state = 'rejected'

    @api.depends('employee_id', 'attendance_id', 'suggested_check_in', 'suggested_check_out', 'ticket_type')
    def _compute_validation(self):
        for ticket in self:
            if not ticket.employee_id or not ticket.suggested_check_in:
                ticket.validation_state = 'warning'
                ticket.validation_message = 'Please provide at least a Check-In time to run the verification.'
                continue

            if ticket.suggested_check_out and ticket.suggested_check_in > ticket.suggested_check_out:
                ticket.validation_state = 'warning'
                ticket.validation_message = 'Warning: Check-In time cannot be later than Check-Out time.'
                continue

            check_out_limit = ticket.suggested_check_out or '2099-12-31 23:59:59'
            domain = [
                ('employee_id', '=', ticket.employee_id.id),
                ('check_in', '<', check_out_limit),
                '|', ('check_out', '=', False), ('check_out', '>', ticket.suggested_check_in)
            ]
            
            if ticket.ticket_type == 'modify':
                if not ticket.attendance_id:
                    ticket.validation_state = 'warning'
                    ticket.validation_message = 'Please select an attendance record to modify.'
                    continue
                domain.append(('id', '!=', ticket.attendance_id.id))

            overlap = self.env['hr.attendance'].search(domain, limit=1)

            if overlap:
                ticket.validation_state = 'warning'
                if ticket.ticket_type == 'modify':
                    ticket.validation_message = f"Warning: These new dates conflict with another existing attendance (Check-In: {overlap.check_in})."
                else:
                    ticket.validation_message = f"Warning: Cannot create this attendance. It overlaps with an existing record (Check-In: {overlap.check_in})."
            else:
                ticket.validation_state = 'valid'
                if ticket.ticket_type == 'modify':
                    ticket.validation_message = 'Looks good! The requested changes are valid and do not overlap with other records.'
                else:
                    ticket.validation_message = 'Looks good! A new attendance record can be safely created with these dates.'