# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import api, exceptions, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
import time


class ActivityAttachments(models.Model):
    _name = 'mail.activity.attachments.files'
    _description = "Mail Activities Attachments Files"

    file = fields.Binary('File', required=True)
    filename = fields.Char('Name')
    attach_id = fields.Many2one('mail.activity.attachments')


class ActivityAttachments(models.Model):
    _name = 'mail.activity.attachments'
    _description = "Mail Activities Attachments"

    notes = fields.Text('Notes', required=True)
    files = fields.Binary('Upload Files')
    filename = fields.Char('File Name')
    res_id = fields.Char('Resource ID')
    res_model = fields.Char('Resource Model')
    res_activity_id = fields.Char('Activity ID')
    related_files_id = fields.One2many('mail.activity.attachments.files', 'attach_id', 'Files')

    @api.onchange('files')
    def onchange_file(self):
        if self.files:
            self.related_files_id = [(0, 0, {
                'file': self.files,
                'filename': str(self.filename)
            })]
            self.files = ''

    def action_add_attachment(self):
        if not self.related_files_id:
            raise ValidationError(_('Please select Files'))
        if self.res_activity_id and self.related_files_id:
            activity = self.env['mail.activity'].browse(int(self.res_activity_id))
            if activity:
                doc_list = ''
                for attach in self.related_files_id:
                    attachment = self.env['ir.attachment'].create({
                        'datas': attach.file,
                        'name': str(attach.filename),
                    })
                    doc_link = '<a href="/web/content/%s?unique=%s&amp;download=true" ' \
                               'class="o_image" title="%s" ' \
                               'data-mimetype="%s"></a>'% (attachment.id, attachment.checksum, attachment.name,
                                                                 attachment.mimetype)
                    doc_list += str(doc_link)
                activity.update({
                        'note': activity.note +"<hr>" + self.notes + "<hr><br></br>" + doc_list
                    })
                activity.action_done()
