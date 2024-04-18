from odoo import fields, models


class ObserveDocumentWizard(models.TransientModel):
    _name = 'observe.document.wizard'
    _description = 'Asistente para la observación de un documento.'

    record_request_line_id = fields.Many2one(comodel_name='record.request.line')
    comment = fields.Text(string='Comentario', required=True)

    def add_comment(self):
        '''
            Creates a record in mail.message with the comment added in the wizard.
            Modify the state of record_request_line_id to observed.
            :return: None
        '''
        record_request_id = self.record_request_line_id.record_request_id
        body = '''
            <p>Observación en adjunto: <strong>{}</strong></p>
            <p>Detalle:</p>
            <p class="text-danger"><strong>{}</strong></p>
        '''.format(self.record_request_line_id.document, self.comment)
        self.env['mail.message'].create({
            'message_type': 'comment',
            'model': 'record.request',
            'res_id': record_request_id.id,
            'subject': f'{record_request_id.op_admission_id.application_number} - {record_request_id.partner_id.name}',
            'subtype_id': self.env.ref('mail.mt_comment').id,
            'author_id': record_request_id.partner_id.id,
            'body': body
        })
        self.record_request_line_id.write({
            'state': 'observed',
            'comment': self.comment
        })
