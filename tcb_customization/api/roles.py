import frappe


def ensure_roles():
    """Create helper roles and assign Attendance Approver to existing HR Manager users.

    Idempotent: safe to run multiple times.
    """
    created = []

    # Ensure Attendance Approver role exists
    if not frappe.db.exists("Role", "Attendance Approver"):
        r = frappe.get_doc({"doctype": "Role", "role_name": "Attendance Approver"})
        r.insert(ignore_permissions=True)
        created.append("Attendance Approver")

    # Optionally create Attendance Viewer role (read-only) if needed
    if not frappe.db.exists("Role", "Attendance Viewer"):
        r2 = frappe.get_doc({"doctype": "Role", "role_name": "Attendance Viewer"})
        r2.insert(ignore_permissions=True)
        created.append("Attendance Viewer")

    # Assign Attendance Approver to users who have HR Manager role
    hr_users = frappe.get_all("Has Role", filters={"role": "HR Manager"}, fields=["parent as user"])
    assigned = 0
    for h in hr_users:
        user = h.get("user") or h.get("parent")
        if not user:
            continue
        # add role using User.add_roles to avoid child table manual creation
        try:
            u = frappe.get_doc("User", user)
            # add_roles handles idempotency
            u.add_roles("Attendance Approver")
            assigned += 1
        except Exception:
            frappe.log_error(f"Failed to assign Attendance Approver to user {user}")

    return {"created_roles": created, "assigned": assigned}


@frappe.whitelist()
def run_ensure_roles():
    if not (("System Manager" in frappe.get_roles()) or ("Administrator" in frappe.get_roles())):
        frappe.throw("Only System Manager or Administrator can run role setup.")
    return ensure_roles()
