import frappe

def execute():
    if frappe.db.exists("Desktop Icon", "My Attendance"):
        return

    icon = frappe.get_doc({
        "doctype": "Desktop Icon",
        "name": "My Attendance",
        "label": "My Attendance",
        "icon_type": "Link",
        "link_type": "External",
        "link": "/desk/employee-attendance",
        "hidden": 0,
        "standard": 1,
        "parent_icon": None,
        "logo_url": "/assets/tcb_customization/images/my-attendance-blue.svg",
    })

    icon.insert(ignore_permissions=True)
    frappe.db.commit()
