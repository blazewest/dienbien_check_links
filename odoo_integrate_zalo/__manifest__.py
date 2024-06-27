# -*- coding: utf-8 -*-
{
    'name': "zalo_message",
    'summary': """
        zalo messager""",
    'description': """
        zalo
    """,
    'author': "HungDD_SGVN",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '1.1',
    # any module necessary for this one to work correctly
    'depends': [
        'base','web'
    ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/zalo_application_views.xml',
        'views/zalo_template.xml',
        'views/fields_zalo_api.xml',
    ],
    'license': 'LGPL-3',
}
