# -*- coding: utf-8 -*-
{
    'name': "chatter",
    'summary': """
        Enhance features of Chatter and applies security
        """,
    'description': """
        This module Enhance features of chatter and applies security on chatter operations
    """,
    'author': "Ksolves",
    'website': "http://www.ksolves.com",

    'category': 'Tool',
    'version': '13.0.1.0.3',
    # any module necessary for this one to work correctly
    'depends': ['base','mail', 'base_setup'],
    # always loaded
    'qweb': [
        'static/src/xml/chatter_edit.xml',
        'static/src/xml/chatter_activity.xml',
    ],
    'data': [
        'security/message_to_customer.xml',
        'security/ir.model.access.csv',
        'views/chatter_assets.xml',
        'views/mail_activity_view.xml',
        'views/mail_activity_attachments_view.xml',
    ],
    'post_init_hook': 'post_install_hook',
}
