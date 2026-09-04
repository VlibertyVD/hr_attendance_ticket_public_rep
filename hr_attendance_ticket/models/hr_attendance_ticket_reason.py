from odoo import models, fields, api

class HrAttendanceTicketReason(models.Model):
    _name = 'hr.attendance.ticket.reason'
    _description = 'Attendance Ticket Reason'

    name = fields.Char(string='Reason', required=True, translate=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
