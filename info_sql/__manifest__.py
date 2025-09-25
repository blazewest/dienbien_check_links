# -*- coding: utf-8 -*-
{
    'name': "info_sql",
    'summary': """
        zalo messager""",
    'description': """
        zalo
    """,
    'author': "HungDD",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '1.1',
    'depends': [
        'check_erro'
    ],
    # always loaded
    'installable': True,
    'application': True,
    'images': ['info/static/src/img/logo.png'],
    'data': [
        'security/ir.model.access.csv',
        'views/database_sql.xml',
    ],
    'license': 'LGPL-3',
}
