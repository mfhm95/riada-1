# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import api, exceptions, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class ChatterMailFollowers(models.Model):
    _inherit = ['mail.followers']

    def _get_recipient_data(self, records, message_type, subtype_id, pids=None, cids=None):
        res = super(ChatterMailFollowers, self)._get_recipient_data(records, message_type, subtype_id, pids=pids,
                                                                    cids=cids)
        date = datetime.now().date()
        data = self.env['mail.activity'].search([('current_mail_follower', '=', True)])
        if data:
            data.current_mail_follower = False
            date = data.date_deadline
        # stop sending notification on activity create schedule
        #Todo Stop only future activities
        if self.env.user.has_group('chatter.hide_future_activity_group') and pids and date > datetime.now().date():
            result = [rec for rec in res if rec[0] == pids[0]]
            if result:
                res.remove(result[0])

        # # stop sending message to customer
        # if not self.env.user.has_group('chatter.message_to_customer_group') and records:
        #     result = [rec for rec in res if rec[0] == records.partner_id.id]
        #     if result:
        #         res.remove(result[0])
        return res
