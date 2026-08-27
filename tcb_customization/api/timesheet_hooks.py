import frappe
from frappe import _


def validate_timesheet(doc, method):
    # Auto-fill employee from logged-in user if not set
    if not doc.get("employee"):
        emp = frappe.get_all(
            "Employee",
            filters={"user_id": frappe.session.user, "status": "Active"},
            fields=["name"],
            limit=1,
        )
        if emp:
            doc.employee = emp[0].name
        else:
            frappe.throw(_("Timesheet must be linked to an Employee. Link your user to an Employee or set the Employee field."))

    # Require description on every timesheet row
    missing_rows = []
    for idx, row in enumerate(doc.get("time_logs") or [], start=1):
        desc = row.description if hasattr(row, "description") else row.get("description") if isinstance(row, dict) else None
        if not (desc and str(desc).strip()):
            missing_rows.append(str(idx))

    if missing_rows:
        frappe.throw(_("Each Timesheet row must have a description. Missing in rows: {rows}").format(rows=", ".join(missing_rows)))
