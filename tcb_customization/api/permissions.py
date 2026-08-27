import frappe


def _require_sys_manager():
    if not (("System Manager" in frappe.get_roles()) or ("Administrator" in frappe.get_roles())):
        frappe.throw("Only System Manager or Administrator can run this setup.")


def apply_attendance_permissions_cli():
    """Apply attendance permissions without requiring a logged-in System Manager (for CLI use)."""
    dt = "Attendance"
    dt_doc = frappe.get_doc("DocType", dt)
    changed = []

    approver_perms = {"permlevel": 0, "read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1}
    viewer_perms = {"permlevel": 0, "read": 1, "write": 0, "create": 0, "submit": 0, "cancel": 0}

    if _ensure_permission_row(dt_doc, "Attendance Approver", approver_perms):
        changed.append("Attendance Approver")
    if _ensure_permission_row(dt_doc, "Attendance Viewer", viewer_perms):
        changed.append("Attendance Viewer")

    if changed:
        dt_doc.save()
        frappe.db.commit()

    return {"changed": changed}


def _ensure_permission_row(dt_doc, role, perms: dict):
    # perms keys: read, write, create, submit, cancel, permlevel
    for p in dt_doc.permissions:
        if p.role == role:
            # update existing
            for k, v in perms.items():
                setattr(p, k, int(bool(v)))
            return False

    dt_doc.append("permissions", {"role": role, **{k: int(bool(v)) for k, v in perms.items()}})
    return True


@frappe.whitelist()
def apply_attendance_permissions():
    """Grant appropriate permissions on `Attendance` for Attendance Approver/Viewer roles.

    - `Attendance Approver`: create, read, write, submit, cancel
    - `Attendance Viewer`: read only
    Idempotent; requires System Manager or Administrator.
    """
    _require_sys_manager()

    dt = "Attendance"
    dt_doc = frappe.get_doc("DocType", dt)
    changed = []

    approver_perms = {"permlevel": 0, "read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1}
    viewer_perms = {"permlevel": 0, "read": 1, "write": 0, "create": 0, "submit": 0, "cancel": 0}

    if _ensure_permission_row(dt_doc, "Attendance Approver", approver_perms):
        changed.append("Attendance Approver")
    if _ensure_permission_row(dt_doc, "Attendance Viewer", viewer_perms):
        changed.append("Attendance Viewer")

    if changed:
        dt_doc.save()
        frappe.db.commit()

    return {"changed": changed}
