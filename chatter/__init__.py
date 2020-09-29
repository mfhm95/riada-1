# -*- coding: utf-8 -*-

from . import models
from odoo.api import Environment, SUPERUSER_ID

def post_install_hook(cr, registry):
    env = Environment(cr, SUPERUSER_ID, {})
    users = {"users": [(4, user_id.id) for user_id in (env['res.users'].search([])) if not user_id.has_group('base.group_system')]}
    chatter_hide_future_activity = env.ref('chatter.hide_future_activity_group')
    chatter_hide_future_activity.write(users)
