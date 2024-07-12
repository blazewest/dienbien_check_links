{
    'name': 'Website Status Checker',
    'version': '1.0',
    'summary': 'Module to check website status',
    'category': 'Tools',
    'author': 'Duy Hung',
    'depends': ['base','os_telegram'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'data/ir_cron_data.xml',
        # 'data/email_template.xml',
        # 'data/server_action.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
