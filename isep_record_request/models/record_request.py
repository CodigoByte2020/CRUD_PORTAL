from odoo import api, fields, models

STATE_SELECTION = [
    ('on_hold', 'En espera'),
    ('accepted', 'Aceptado'),
    ('observed', 'Observado'),
]


class RecordRequest(models.Model):
    _name = 'record.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'op_admission_id'

    op_admission_id = fields.Many2one(comodel_name='op.admission', string='Admisión', required=True)
    partner_id = fields.Many2one(related='op_admission_id.partner_id', store=True)
    batch_id = fields.Many2one(related='op_admission_id.batch_id')
    course_id = fields.Many2one(related='op_admission_id.course_id')
    application_number = fields.Char(related='op_admission_id.application_number')
    record_request_list_id = fields.Many2one(comodel_name='record.request.list',
                                             string='Lista de solicitudes de registro', required=True)
    description = fields.Html(string='Descripción')
    record_request_line_ids = fields.One2many(comodel_name='record.request.line', inverse_name='record_request_id',
                                              string='Adjuntos')
    state = fields.Selection(selection=STATE_SELECTION, default='on_hold', string='Estado', compute='_compute_state',
                             store=True, tracking=True)
    hide_status = fields.Boolean(default=False)

    @api.depends('record_request_line_ids.state')
    def _compute_state(self):
        for record_request in self:
            record_request_line_status = record_request.record_request_line_ids.mapped(lambda x: x.state)
            if all(state == 'accepted' for state in record_request_line_status):
                record_request.write({'state': 'accepted'})
            elif any(state == 'observed' for state in record_request_line_status):
                record_request.write({'state': 'observed'})
            else:
                record_request.write({'state': 'on_hold'})

    def action_confirm(self):
        record_request_line_ids = [(5, 0, 0)]
        record_request_line_ids.extend(
            [(0, 0, {'document': line.document}) for line in self.record_request_list_id.record_request_list_line_ids])
        self.write({
            'record_request_line_ids': record_request_line_ids,
            'hide_status': True
        })
