from odoo import fields, models


class RecordRequestListLine(models.Model):
    _name = 'record.request.list.line'

    document = fields.Char(string='Documento')
    record_request_list_id = fields.Many2one(comodel_name='record.request.list')
