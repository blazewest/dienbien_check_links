# -*- coding: utf-8 -*-
{

    'name': "Code Generator for Telegram Integration",

    'summary': """
        With single line of code that we will generate for you , it provides sending from your Telegram bot to your channel
       """,
    'description': """
        Usage : 
        1 - Create Telegram Channel 
        2 - Create Telegram Bot using BotFather
        3 - Copy One line of code to send to a Telegram Channel
    """,
    'author': "Odoo Station",
    'website': "https://t.me/odoochat/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list

    'category': 'Productivity',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
        'views/telebot.xml',
    ],
    # only loaded in demonstration mode


    'external_dependencies': {
        'python': ['clipboard'],
    },
    'images': ['images/main_screenshot.png'],
    'license': 'LGPL-3',

}
