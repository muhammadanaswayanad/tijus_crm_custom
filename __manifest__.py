{
    'name': 'Tijus CRM Customizations',
    'version': '17.0.1.0.0',
    'category': 'CRM',
    'summary': 'Custom CRM enhancements for Tijus',
    'description': """
Custom CRM module with additional features:
- Editable closed date
- Country detection from phone numbers with flag display
    """,
    'author': 'Tijus',
    'depends': ['crm'],  # Add 'sale_crm' if you need sale integration
    'data': [
        'views/crm_views.xml',  # Load this first
        'views/crm_lead_views.xml',  # Then load your working view
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
