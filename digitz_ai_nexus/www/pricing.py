no_cache = 1

import frappe


def get_context(context):
    context.sitename = frappe.local.site
    context.socketio_port = frappe.conf.socketio_port or 9000
    context.site_widget_code = frappe.conf.site_widget_code or "DIGITZ-AI-NEXUS-SITE"
    context.dev_server = frappe.conf.developer_mode or 0
