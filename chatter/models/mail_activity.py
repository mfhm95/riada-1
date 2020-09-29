# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class ChatterMailActivity(models.Model):
    _inherit = 'mail.activity'

    def _default_datetime(self):
        return fields.Datetime.to_string(fields.Datetime.now())

    is_readonly = fields.Boolean(default=False)
    start_datetime = fields.Datetime('Start Date', required=True,default=_default_datetime)
    start_date = fields.Date('Start Date', required=True)
    datetime_deadline = fields.Datetime('Due Date', required=True,default=_default_datetime)
    is_chatter_active = fields.Boolean(string='Is Chatter Active', default=False,
                                       compute="_is_chatter_active")
    current_mail_follower = fields.Boolean(default=False)

    @api.onchange('start_datetime','datetime_deadline')
    def is_startdate_valid(self):
        if self.start_datetime > self.datetime_deadline:
            self.datetime_deadline = self.start_datetime
            raise ValidationError(_("Start datetime must be eariler than Due datetime"))

    def action_done(self):
        self.action_notify_chatter()
        super(ChatterMailActivity, self).action_done()

    def _is_chatter_active(self):
        for rec in self:
            if self.env.user.id == rec.create_uid.id or self.env.user.has_group('base.group_system'):
                rec.is_chatter_active = True
            else:
                rec.is_chatter_active = False

    def write(self, values):
        res = super(ChatterMailActivity, self).write(values)
        if values.get('user_id') or values.get('note') or values.get('date_deadline') or values.get(
                'summary') or values.get('activity_type_id'):
            self.current_mail_follower = True
            if not self.env.context.get('mail_activity_quick_update', False):
                self.action_notify_chatter()
            for activity in self:
                self.env[activity.res_model].browse(activity.res_id).message_subscribe(
                    partner_ids=[activity.user_id.partner_id.id])
                if activity.date_deadline <= fields.Date.today():
                    self.env['bus.bus'].sendone(
                        (self._cr.dbname, 'res.partner', activity.user_id.partner_id.id),
                        {'type': 'activity_updated', 'activity_created': True})
            for activity in self:
                if activity.date_deadline <= fields.Date.today():
                    pre_responsibles = self.mapped('user_id.partner_id')
                    for partner in pre_responsibles:
                        self.env['bus.bus'].sendone(
                            (self._cr.dbname, 'res.partner', partner.id),
                            {'type': 'activity_updated', 'activity_deleted': True})
        return res

    def action_notify_chatter(self):
        if not self:
            return
        original_context = self.env.context
        body_template = self.env.ref('mail.message_activity_assigned')
        for activity in self:
            if activity.user_id.lang:
                # Send the notification in the assigned user's language
                self = self.with_context(lang=activity.user_id.lang)
                body_template = body_template.with_context(lang=activity.user_id.lang)
                activity = activity.with_context(lang=activity.user_id.lang)
            model_description = self.env['ir.model']._get(activity.res_model).display_name
            body = body_template.render(
                dict(activity=activity, model_description=model_description),
                engine='ir.qweb',
                minimal_qcontext=True
            )
            record = self.env[activity.res_model].browse(activity.res_id)
            if activity.user_id:
                record.message_notify(
                    partner_ids=activity.create_uid.ids,
                    body=body,
                    subject=_('%s: %s assigned to you') % (activity.res_name, activity.summary or activity.activity_type_id.name),
                    record_name=activity.res_name,
                    model_description=model_description,
                    email_layout_xmlid='mail.mail_notification_light',
                )
            body_template = body_template.with_context(original_context)
            self = self.with_context(original_context)

    def _compute_has_recommended_activities(self):
        for rec in self:
            rec.is_readonly = False if self.env.user.has_group('base.group_system') or self.env.uid == rec.create_uid.id else True
        return super(ChatterMailActivity, self)._compute_has_recommended_activities()

    @api.onchange('activity_type_id')
    def _onchange_activity_type_id(self):
        if self.activity_type_id:
            self.summary = self.activity_type_id.summary
            # Date.context_today is correct because date_deadline is a Date and is meant to be
            # expressed in user TZ
            base = fields.Date.context_today(self)
            if self.activity_type_id.delay_from == 'previous_activity' and 'activity_previous_deadline' in self.env.context:
                base = fields.Date.from_string(self.env.context.get('activity_previous_deadline'))
            self.date_deadline = base + relativedelta(
                **{self.activity_type_id.delay_unit: self.activity_type_id.delay_count})
            self.datetime_deadline = self.datetime_deadline + relativedelta(
                **{self.activity_type_id.delay_unit: self.activity_type_id.delay_count})
            self.user_id = self.activity_type_id.default_user_id or self.env.user
            if self.activity_type_id.default_description:
                self.note = self.activity_type_id.default_description

    @api.onchange('datetime_deadline', 'start_datetime')
    def _onchange_datetime_deadline(self):
        if self.datetime_deadline:
            self.date_deadline = self.datetime_deadline.date()
        if self.start_datetime:
            self.start_date = self.start_datetime.date()


class MailMessageInherited(models.Model):
    _inherit = 'mail.message'

    current_user = fields.Many2one('res.users')

    def write(self, vals):
        vals.update({'current_user': self.env.user.id})
        res = super(MailMessageInherited, self).write(vals)
        return res

    def message_format(self):
        res = super(MailMessageInherited, self).message_format()
        for rec in res:
            rec.update({
                'current_user': self.env['mail.message'].browse(rec.get('id')).current_user.name
            })
        return res
