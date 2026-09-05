{
    'name': 'Attendance Adjustment Tickets',
    'version': '19.0.1.0.1',
    'category': 'Human Resources/Attendances',
    'images': ['static/description/banner.png'],
    'summary': 'Allow employees to create tickets for missed check-ins/outs.',
    'description': """
        Attendance incidence management module.
        Allows employees to report justifications when they:
        - Forget to check in or check out.
        - Miss their attendance records for the entire workday.
    """,
    'author': 'Daniel Venegas',
    'maintainer': 'Daniel Venegas',
    'license': 'LGPL-3',
    'depends': ['hr_attendance', 'mail'],
    'data': [
        #security
        'security/attendance_ticket_groups.xml',
        'security/ir.model.access.csv',
        'security/attendance_ticket_rules.xml',

        #data
        'data/ir_sequence_data.xml',        
        'data/attendance_ticket_reason_data.xml',        

        #views
        'views/hr_employee_views.xml',
        'views/attendance_ticket_views.xml',
        'views/attendance_ticket_reason_views.xml',
        'views/hr_employee_puplic_views.xml',
        'views/ir_menu_views.xml',
        
        
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}