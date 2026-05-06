import frappe


def after_install():
    create_default_access_policies()


def create_default_access_policies():
    from digitz_ai_nexus.api.setup import create_default_access_policies

    create_default_access_policies()