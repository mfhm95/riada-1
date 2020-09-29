# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def create(self, vals_list):
        res = super(ResUsers, self).create(vals_list)

        if not res.user_has_groups('base.group_system'):
            chatter_hide_future_activity = self.env.ref('chatter.hide_future_activity_group')
            chatter_hide_future_activity.write(res)
        return res
