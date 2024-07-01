# -*- coding: utf-8 -*-
{

    'name': "Telegram",

    'summary': """
        With single line of code that we will generate for you , it provides sending from your Telegram bot to your channel
       """,
    'description': """
        Usage : 
        1 - Create Telegram Channel 
        2 - Create Telegram Bot using BotFather
        3 - Copy One line of code to send to a Telegram Channel
    """,
    'author': "Dao Duy Hung",
    'website': "",

    'category': 'Productivity',
    'version': '0.1',
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
        'views/telebot.xml',
    ],

    'external_dependencies': {
        'python': ['clipboard'],
    },
    'images': ['images/main_screenshot.png'],
    'license': 'LGPL-3',

}
