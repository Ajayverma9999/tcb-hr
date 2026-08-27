import frappe
from frappe.utils import getdate, today
from .custom_fields import ensure_hr_custom_fields


def validate_leave_notice(doc, method):
    # Ensure custom fields exist (idempotent)
    try:
        ensure_hr_custom_fields()
    except Exception:
        pass

    # Skip if dates are not selected
    if not doc.from_date or not doc.to_date:
        return

    # Allow HR override flag or HR role to bypass
    if getattr(doc, "hr_override", False) or ("HR Manager" in frappe.get_roles()):
        return

    apply_date = getdate(today())
    from_date = getdate(doc.from_date)
    to_date = getdate(doc.to_date)

    # Calculate total leave days
    leave_days = (to_date - from_date).days + 1

    # Days between application date and leave start date
    notice_days = (from_date - apply_date).days

    # Read per-leave-type configured advance notice if present
    lt_notice = frappe.get_value("Leave Type", doc.leave_type, "advance_notice_days")

    # If Leave Type doesn't define advance notice, fall back to HR Settings default then legacy rules
    required_notice = 0
    if lt_notice:
        required_notice = lt_notice
    else:
        try:
            hr = frappe.get_single('HR Settings')
            default_adv = hr.get('leave_default_advance_days')
            if default_adv:
                required_notice = int(default_adv)
        except Exception:
            required_notice = 0

    # Fallback legacy rules when still not configured
    if not required_notice:
        if leave_days == 2:
            required_notice = 3
        elif 3 <= leave_days <= 4:
            required_notice = 7
        elif 5 <= leave_days <= 6:
            required_notice = 15
        elif leave_days >= 7:
            required_notice = 30

    # No validation for 1-day leave or zero-config
    if required_notice == 0:
        return

    # Validate advance notice
    if notice_days < required_notice:
        frappe.throw(
            f"""
            <b>Advance Leave Notice Required</b><br><br>

            As per the company leave policy, this leave request must be submitted at least
            <b>{required_notice} day(s)</b> before the leave start date.

            <br><br>

            For emergency leave, please contact your Reporting Manager or HR.
            """,
            title="Leave Policy",
        )
def validate_manager_verification(doc, method):
    """HR ko Approve karne se pehle Manager Verified checkbox tick hona chahiye"""
    if doc.status == "Approved" and not doc.get("custom_manager_verified"):
        frappe.throw("Cannot approve this leave until the Reporting Manager has verified it (Manager Verified checkbox).")
