import frappe
from frappe.utils import nowdate


def get_pending_employees():
    today = nowdate()
    employees = frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "employee_name", "user_id", "company"]
    )
    pending = []
    for emp in employees:
        ts = frappe.db.exists(
            "Timesheet",
            {"employee": emp.name, "docstatus": 1, "start_date": today}
        )
        if not ts:
            pending.append(emp)
    return pending


def notify(emp, title, message):
    if not emp.user_id:
        return
    frappe.get_doc({
        "doctype": "Notification Log",
        "subject": title,
        "email_content": message,
        "for_user": emp.user_id,
        "type": "Alert"
    }).insert(ignore_permissions=True)


def first_reminder():
    try:
        hr = frappe.get_single("HR Settings")
        if not hr.get("timesheet_reminder_enabled"):
            return
    except Exception:
        pass
    for emp in get_pending_employees():
        notify(emp, "Timesheet Reminder", "Please submit today's Timesheet before 11:55 PM.")


def final_reminder():
    try:
        hr = frappe.get_single("HR Settings")
        if not hr.get("timesheet_reminder_enabled"):
            return
    except Exception:
        pass
    for emp in get_pending_employees():
        notify(
            emp,
            "Final Reminder",
            "Only 25 minutes are left. Submit today's Timesheet before 11:55 PM. Missing timesheets will be sent to HR for review; pay is never docked automatically."
        )


def mark_lwp():
    # Do NOT auto-apply LWP or mark any attendance here.
    # A missing timesheet is never treated as an automated absence. Instead,
    # we simply notify the employee; the actual case is picked up by the
    # HR review queue (see attendance_job.process_previous_day /
    # get_pending_reviews), where HR must explicitly decide Present/Absent.
    for emp in get_pending_employees():
        notify(
            emp,
            "Timesheet Missing",
            "Today's Timesheet was not submitted. This has been sent to HR for review; no automatic Leave Without Pay has been applied."
        )
