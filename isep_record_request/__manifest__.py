{
    'name': 'Solicitudes de registro',
    'summary': 'Módulo de solicitudes de registro.',
    'description': 'Módulo para la gestión de solicitudes de registro.',
    'author': 'Contreras Pumamango Gianmarco - gmcontrpuma@gmail.com',
    'website': 'https://github.com/CodigoByte2020',
    'category': 'Tools',
    'version': '16.0.0.0.1',
    'depends': [
        'openeducat_admission',
        'portal'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/isep_record_request_menus.xml',
        'views/record_request_views.xml',
        'views/record_request_list_views.xml',
        'views/portal_templates.xml',
        'wizards/observe_document_views.xml'
    ],
    'installable': True,
}
