import frappe

def run():
    pages = frappe.get_all("Page", fields=["name", "title", "route", "module"], limit=50)
    for p in pages:
        print(f"name={p.name!r} title={p.title!r} route={p.route!r} module={p.module!r}")
