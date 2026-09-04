from odoo import models, fields

class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    attendance_ticket_count = fields.Integer(
        compute='_compute_attendance_ticket_count',
        string='Tickets'
    )

    def _compute_attendance_ticket_count(self):
        for employee in self:
            employee.attendance_ticket_count = self.env['hr.attendance.ticket'].search_count([
                ('employee_id.user_id', '=', employee.user_id.id)
            ])