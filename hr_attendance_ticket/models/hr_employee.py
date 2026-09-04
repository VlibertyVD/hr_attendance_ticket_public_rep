from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    attendance_ticket_count = fields.Integer(
        compute='_compute_attendance_ticket_count',
        string='Tickets'
    )

    def _compute_attendance_ticket_count(self):
        for employee in self:

            employee.attendance_ticket_count = self.env['hr.attendance.ticket'].search_count([
                ('employee_id', '=', employee.id)
            ])