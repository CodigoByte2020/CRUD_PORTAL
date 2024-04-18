from odoo import fields, http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from collections import OrderedDict
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.tools import date_utils, groupby as groupbyelem
from operator import itemgetter
from odoo.addons.portal.controllers.mail import _message_post_helper
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from odoo.osv.expression import OR

import json
import base64

class CustomerPortal(portal.CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        user = request.env.user
        Attachment = request.env['ir.attachment'].sudo()
        if 'documents_count' in counters:
            domain = []        
            domain += [('res_model', 'not in', ['ir.ui.view','ir.module.module'])]
            domain += ['|',('create_uid', '=', user.id),('shared_user_ids','in',[user.id])]
            documents_count = Attachment.sudo().search_count(domain) \
                if Attachment.sudo().check_access_rights('read', raise_exception=False) else 0
            values['documents_count'] = documents_count if documents_count else '0'
        return values
    
    @http.route(['/my/documents', '/my/documents/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_documents(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='all', groupby='none', **kw):
        values = self._prepare_portal_layout_values()
        user = request.env.user
        Attachment = request.env['ir.attachment'].sudo()
        
        domain = [
            ('res_model', 'not in', ['ir.ui.view','ir.module.module']),
            '|',('create_uid', '=', user.id),('shared_user_ids','in',[user.id])]        
        
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
            
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc, id desc'},
            'name': {'label': _('Name'), 'order': 'name asc, id asc'},
        }
        
        # default sortby order
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'personal_documents': {'label': _('Personal Documents'), 'domain': [('is_personal_directory', '=', True)]},
            'portal_documents': {'label': _('Portal Documents'), 'domain': [('is_portal_directory', '=', True)]},
            'shared_documents': {'label': _('Shared Documents'), 'domain': [('shared_user_ids','in',[user.id]),('create_uid','not in',[user.id])]},
        }
        
        searchbar_inputs = {
            'all': {'input': 'all', 'label': _('Search in All')},
            'name': {'input': 'name', 'label': _('Search in Name')},
            'code': {'input': 'code', 'label': _('Search in Code')},
            'description': {'input': 'description', 'label': _('Search in Description')},
            'create_date': {'input': 'create_date', 'label': _('Search in Create Date')},
            'mimetype': {'input': 'mimetype', 'label': _('Search in Mime Type')},
            'folder_id': {'input': 'folder_id', 'label': _('Search in Folder')},
        }
        
        searchbar_groupby = {
            'none': {'input': 'none', 'label': _('None')},
            'folder_id': {'input': 'folder_id', 'label': _('Folder')},        
        }
        
        # search
        if search and search_in:
            search_domain = []
            if search_in in ('name', 'all'):
                search_domain = OR([search_domain, [('name', 'ilike', search)]])
            if search_in in ('code', 'all'):
                search_domain = OR([search_domain, [('code', 'ilike', search)]])
            if search_in in ('description', 'all'):
                search_domain = OR([search_domain, [('description', 'ilike', search)]])
            if search_in in ('create_date', 'all'):
                search_domain = OR([search_domain, [('create_date', 'ilike', search)]])
            if search_in in ('mimetype', 'all'):
                search_domain = OR([search_domain, [('mimetype', 'ilike', search)]])
            if search_in in ('folder_id', 'all'):
                search_domain = OR([search_domain, [('folder_id', 'ilike', search)]])
            domain += search_domain
    
        # count for pager
        documents_count = Attachment.search_count(domain)
        
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        
        # make pager
        pager = portal_pager(
            url="/my/documents",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby, 'groupby': groupby, 'search_in': search_in, 'search': search},
            total=documents_count,
            page=page,
            step=self._items_per_page
        )
        
        if groupby == 'folder_id':
            order = "folder_id, %s" % order
                
        # search the dcouemnts to display, according to the pager data
        documents = Attachment.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        
        if groupby == 'none':
            grouped_documents = []
            if documents:
                grouped_documents = [documents]
        else:
            grouped_documents = [Attachment.sudo().concat(*g) for k, g in groupbyelem(documents, itemgetter('folder_id'))]
        
        
        request.session['my_documents_history'] = documents.ids[:100]
        values.update({
            'date': date_begin,            
            'date': date_begin,
            'date_end': date_end,
            'documents': documents.sudo(),
            'grouped_documents': grouped_documents,
            'page_name': 'documents',
            'default_url': '/my/documents',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_groupby': searchbar_groupby,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'search': search,
            'sortby': sortby,
            'groupby': groupby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,                        
            'base_url': http.request.env["ir.config_parameter"].sudo().get_param("web.base.url"),
        })
        return request.render("documents_portal_management.portal_my_documents", values)
        
    @http.route(['/my/documents/upload_portal_documents'], type='http', auth="user", website=True)
    def upload_portal_documents(self, access_token=None):
        if not request.session.uid:
            return {'error': 'anonymous_user'}
        
        user = request.env.user
        values = {
            'user': user,
            'page_name': 'upload_portal_documents',
        }
        return request.render("documents_portal_management.my_attendance_upload_portal_documents", values)
    
    @http.route(['/my/documents/upload_portal_documents/upload'], type='http', auth="public", methods=['POST'], website=True)
    def portal_documents_upload(self, **post):
        user = request.env.user
        user_sudo = request.env['res.users'].sudo().browse(user.id)
        portal_directory = request.env.ref('documents_portal_management.portal_folder')
        try:            
            file = post.get('upload_documents', '')
            stream = file.stream
            fread = stream.read()
            attach_vals = {
                'name': file.filename,
                'folder_id': portal_directory and portal_directory.id or False,
                'res_name': file.filename,
                'res_model': 'res.partner',
                'res_id': user_sudo and user_sudo.partner_id.id or False,
                'partner_id': user_sudo and user_sudo.partner_id.id or False,
                'datas': base64.encodebytes(fread),
            }
            create = request.env['ir.attachment'].sudo().create(attach_vals)
        except ValidationError as e:
            return json.dumps({'error_fields' : e.args[0]})
        except Exception as e:
            return json.dumps({'Error' : _('Sorry, but the uploaded file is either invalid or too large! Reason: %s') % (e,)})
        
        return request.redirect('/my/documents')