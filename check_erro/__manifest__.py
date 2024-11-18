{
    'name': 'Website Status Checker',
    'version': '1.0',
    'summary': 'Module to check website status',
    'category': 'Tools',
    'author': 'Duy Hung',
    'depends': ['base','os_telegram','mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/views_ip_wan.xml',
        'views/views_qr_code.xml',
        # 'data/email_template.xml',
        # 'data/server_action.xml',

        'views/disk_info.xml',
        'views/http_response.xml',
        'views/loginattempt.xml',
        'views/port_response.xml',
        'views/telegraf_data_view.xml',
    ],
    'images': ['check_erro/static/src/img/logo.png'],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
    'assets': {
            'web.assets_backend': [
                'check_erro/static/src/img/logo.png',
                'check_erro/static/src/css/kanban_style.css',
            ],
        },
}
