import base64
import logging

from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal, pager
from odoo.http import request
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CustomerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super(CustomerPortal, self)._prepare_home_portal_values(counters)
        user_id = request.env.uid
        current_user = request.env['res.users'].sudo().browse(user_id)
        domain = [
            ('partner_id', '=', current_user.partner_id.id),
            ('op_admission_id.state', '=', 'done')
        ]
        values['requests_quantity'] = request.env['record.request'].sudo().search_count(domain)  # FIXME: CUANDO HAY 0 NO SE MUESTRA :(
        return values

    @http.route(['/my/requests', '/my/requests/page/<int:page>'], type='http', website=True)
    def record_request_list_view(self, page=1, **kwargs):
        step = 10
        record_request_model = request.env['record.request'].sudo()
        user_id = request.env.uid
        current_user = request.env['res.users'].sudo().browse(user_id)
        domain = [
            ('partner_id', '=', current_user.partner_id.id),
            ('op_admission_id.state', '=', 'done')
        ]
        my_requests_quantity = record_request_model.search_count(domain)
        page_detail = pager(
            url='/my/requests',
            total=my_requests_quantity,
            page=page,
            step=step
        )
        my_requests = record_request_model.search(domain, limit=step, offset=page_detail['offset'])
        success_message = request.params.get('success_message', False)
        error_message = request.params.get('error_message', False)
        values = {
            'my_requests': my_requests,
            'page_name': 'request_list_view',
            'pager': page_detail,
            'success_message': success_message,
            'error_message': error_message
        }
        return request.render('isep_record_request.record_request_list_view', values)

    @http.route('/my/requests/<int:record_request_id>', type='http', methods=['GET', 'POST'], website=True)
    def record_request_form_view(self, record_request_id, **kwargs):
        record_request_model = request.env['record.request'].sudo()
        current_request = record_request_model.browse(record_request_id)
        values = {
            'current_request': current_request,
            'page_name': 'record_request_form_view'
        }

        if request.httprequest.method == 'GET':
            user_id = request.env.uid
            current_user = request.env['res.users'].sudo().browse(user_id)
            domain = [
                ('partner_id', '=', current_user.partner_id.id),
                ('op_admission_id.state', '=', 'done')
            ]
            record_request_ids = record_request_model.search(domain).ids
            record_request_index = record_request_ids.index(record_request_id)
            values.update({
                'prev_record': record_request_index != 0 and f'/my/requests/{record_request_ids[record_request_index - 1]}',
                'next_record': record_request_index < len(record_request_ids) - 1 and f'/my/requests/{record_request_ids[record_request_index + 1]}'
            })
            return request.render('isep_record_request.record_request_form_view', values)

        elif request.httprequest.method == 'POST':
            url = self.update_record_request(kwargs)
            return request.redirect(url)

    def update_record_request(self, kwargs):
        '''
            Update attachments for each document.
            :param kwargs: Arguments to update.
            :type kwargs: Dictionary.
            :return: A string that represents the url to be redirected.
            :rtype: str
        '''
        url = ''
        documents_to_update = [{'document_id': int(key.split('update_document_')[1]), 'file': value}
                               for key, value in kwargs.items() if key.startswith('update_document_')]
        try:
            for document in documents_to_update:
                stream = document['file'].stream
                read_file = stream.read()
                record_request_line = request.env['record.request.line'].sudo().browse(document['document_id'])
                decoded_file = base64.encodebytes(read_file)
                if decoded_file:
                    record_request_line.write({
                        'file': decoded_file,
                        'filename': document['file'].filename,
                        'state': 'on_hold'
                    })
            success_message = 'Documento(s) actualizados con éxito'
            url = f'/my/requests?success_message={success_message}'

        except ValidationError as exception:
            _logger.error(f'******************* ACTUALIZACIÓN DE SOLICITUD FALLIDA *******************')
            _logger.error(f'***************** Valores de campos incorrectos. Razón: {exception} *****************')

            error_message = f'Actualización de solicitud fallida: \nValores de campos incorrectos. \nRazón: {exception}'
            url = f'/my/requests?error_message={error_message}'

        except Exception as exception:
            _logger.error(f'******************* ACTUALIZACIÓN DE SOLICITUD FALLIDA *******************')
            _logger.error(f'****** El archivo subido no es válido o es demasiado grande. Razón: {exception} ******')

            error_message = f'Actualización de solicitud fallida: \nEl archivo subido no es válido o es demasiado ' \
                            f'grande. \nRazón: {exception}'
            url = f'/my/requests?error_message={error_message}'

        finally:
            return url

    @http.route('/my/requests/documents', type='http', methods=['GET'], auth='public', website=True)
    def document_form_view(self, **kwargs):
        record_request_list = request.env['record.request.list'].sudo().search([])
        user_id = request.env.uid
        current_user = request.env['res.users'].sudo().browse(user_id)
        domain = [
            ('partner_id', '=', current_user.partner_id.id),
            ('state', '=', 'done')
        ]
        admissions = request.env['op.admission'].sudo().search(domain)
        values = {
            'page_name': 'document_form_view',
            'record_request_list': record_request_list,
            'admissions': admissions
        }
        return request.render('isep_record_request.document_form_view', values)

    @http.route('/my/requests/new_request', type='http', methods=['GET', 'POST'], auth='public', website=True)
    def new_request_form_view(self, **kwargs):
        record_request_list_model = request.env['record.request.list'].sudo()
        op_admission_model = request.env['op.admission'].sudo()
        values = {
            'page_name': 'new_request_form_view',
            'record_request_line_ids': []
        }

        if request.httprequest.method == 'GET':
            record_request_list_id = kwargs.get('documents', False)
            admission_id = kwargs.get('admissions', False)
            if record_request_list_id:
                record_request_list = record_request_list_model.browse(int(record_request_list_id))
                record_request_list_line_ids = record_request_list.record_request_list_line_ids
                values.update({
                    'record_request_list': record_request_list,
                    'record_request_list_line_ids': record_request_list_line_ids
                })
            if admission_id:
                admission = op_admission_model.browse(int(admission_id))
                values.update({
                    'admission': admission,
                    'partner_id': admission.partner_id,
                    'batch_id': admission.batch_id,
                    'course_id': admission.course_id,
                    'application_number': admission.application_number
                })
            return request.render('isep_record_request.new_request_form_view', values)

        elif request.httprequest.method == 'POST':
            values_request = {}
            if kwargs.get('documents', False):
                record_request_list = record_request_list_model.browse(int(kwargs['documents']))
                values_request['record_request_list'] = record_request_list.id
            if kwargs.get('admissions', False):
                op_admission_id = op_admission_model.browse(int(kwargs['admissions']))
                values_request.update({
                    'op_admission_id': op_admission_id.id,
                    'partner_id': op_admission_id.partner_id.id
                })
            url = self.create_record_request(kwargs)
            return request.redirect(url)

    def create_record_request(self, kwargs):
        '''
            Create new request with their respective documents.
            :param kwargs: Arguments to create the new record request.
            :type kwargs: Dictionary.
            :return: A string that represents the url to be redirected.
            :rtype: str
        '''
        record_request_model = request.env['record.request'].sudo()
        op_admission_model = request.env['op.admission'].sudo()
        documents = [value for key, value in kwargs.items() if key.startswith('upload_document_')]
        record_request_line_ids = []
        record_request_list_id, op_admission_id, partner_id = 0, 0, 0
        url = ''

        if kwargs.get('documents', False):
            record_request_list_id = int(kwargs['documents'])
        if kwargs.get('admissions', False):
            op_admission = op_admission_model.browse(int(kwargs['admissions']))
            op_admission_id = op_admission.id
            partner_id = op_admission.partner_id.id

        try:
            new_record_request = record_request_model.create({
                'record_request_list_id': record_request_list_id,
                'op_admission_id': op_admission_id,
                'partner_id': partner_id
            })
            for document in documents:
                stream = document.stream
                read_file = stream.read()
                decoded_file = base64.encodebytes(read_file)
                if decoded_file:
                    record_request_line_ids.extend([(0, 0, {
                        'record_request_id': new_record_request.id,
                        'document': document.name.split('upload_document_')[1],
                        'filename': document.filename,
                        'file': decoded_file
                    })])
            new_record_request.write({'record_request_line_ids': record_request_line_ids})
            success_message = 'Solicitud registrada con éxito'
            url = f'/my/requests?success_message={success_message}'

        except ValidationError as exception:
            _logger.error(f'******************* CREACIÓN DE SOLICITUD FALLIDA *******************')
            _logger.error(f'******************* Valores de campos incorrectos. Razón: {exception} *******************')

            error_message = f'Creación de solicitud fallida: \nValores de campos incorrectos. \nRazón: {exception}'
            url = f'/my/requests?error_message={error_message}'

        except Exception as exception:
            _logger.error(f'******************* CREACIÓN DE SOLICITUD FALLIDA *******************')
            _logger.error(f'******** El archivo subido no es válido o es demasiado grande. Razón: {exception} ********')

            error_message = f'Creación de solicitud fallida: \nEl archivo subido no es válido o es demasiado grande. ' \
                            f'\nRazón: {exception}'
            url = f'/my/requests?error_message={error_message}'

        finally:
            return url
