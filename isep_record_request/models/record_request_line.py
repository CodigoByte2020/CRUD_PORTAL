from odoo import fields, models

STATE_SELECTION = [
    ('on_hold', 'En espera'),
    ('accepted', 'Aceptado'),
    ('observed', 'Observado'),
]


class RecordRequestLine(models.Model):
    _name = 'record.request.line'

    record_request_id = fields.Many2one(comodel_name='record.request', string='Solicitud')
    document = fields.Char(string='Documento', readonly=True)
    filename = fields.Char(string='Nombre de archivo')
    file = fields.Binary(attachment=True, string='Archivo')
    state = fields.Selection(selection=STATE_SELECTION, default='on_hold', string='Estado')  # TODO: FALTA MANEJAR LA VISIBIVILIDAD DE LOS BOTONES
    comment = fields.Text(string='Comentario')

    def action_observe(self):
        view_id = self.env.ref('isep_record_request.observe_document_wizard_view_form').id
        return {
            'name': 'Observar documento',
            'type': 'ir.actions.act_window',
            'res_model': 'observe.document.wizard',
            'view_mode': 'form',
            'view_id': view_id,
            'views': [(view_id, 'form')],
            'target': 'new',
            'context': {'default_record_request_line_id': self.id}
        }

    def action_accept(self):
        self.write({'state': 'accepted'})
