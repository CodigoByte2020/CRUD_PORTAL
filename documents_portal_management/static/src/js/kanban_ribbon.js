/** @odoo-module */

import { registry } from "@web/core/registry";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

const { Component } = owl;

class KanbanRibbonWidget extends Component {
    get classes() {
        let classes = this.props.bg_color;
        classes += " content";
        if (this.props.text.length > 15) {
            classes += " o_small";
        } else if (this.props.text.length > 10) {
            classes += " o_medium";
        }
        return classes;
    }    
}

KanbanRibbonWidget.template = "documents_portal_management.kanban_ribbon";
KanbanRibbonWidget.props = {
    ...standardWidgetProps,
    text: { type: String , optional: true },
    icon : { type: String, optional: true },
    bg_color: { type: String, optional: true },
};
KanbanRibbonWidget.defaultProps = {
    text: "",
    icon: "fa fa-share",
    bg_color: "bg-success",
};
KanbanRibbonWidget.extractProps = ({ attrs }) => {
    return {
        text: attrs.title || attrs.text,
        icon: attrs.icon,
        bg_color: attrs.bg_color,
    };
};

registry.category("view_widgets").add("kanban_ribbon", KanbanRibbonWidget);
