{
    'name': 'Tijus CRM Customizations',
    'version': '1.0',
    'category': 'Sales/CRM',
    'summary': 'Custom enhancements for CRM module',
    'description': """
        This module adds country detection from phone numbers in CRM leads.
        Features:
        - Auto-detect country from phone numbers
        - Display country flags in kanban view
    """,
    'depends': ['crm'],
    'data': [
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
