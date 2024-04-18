/** @odoo-module **/

import SearchPanel from "web.searchPanel";
import { patch } from 'web.utils';
const { _t } = require('web.core');

patch(SearchPanel.prototype, 'documents_portal_management.SearchPanel', {
    setup() {
        this._super();
    }
});