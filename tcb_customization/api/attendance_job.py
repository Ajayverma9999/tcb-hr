import frappe
from frappe.utils import add_days, nowdate, getdate
from datetime import timedelta

from hrms.hr.doctype.attendance.attendance import mark_attendance
from frappe.utils.background_jobs import enqueue
import json


def _ensure_hr_role():
    # Allow HR Manager, System Manager, or Attendance Approver role
    if not (("HR Manager" in frappe.get_roles()) or ("System Manager" in frappe.get_roles()) or ("Attendance Approver" in frappe.get_roles())):
        frappe.throw("Only HR Manager, System Manager, or Attendance Approver can perform this action.", frappe.PermissionError)


def process_previous_day():
    """Create Attendance for employees who submitted Timesheet yesterday.

    Do NOT mark Absent for missing timesheets; those are left for HR review.
    """
    prev_date = add_days(nowdate(), -1)

    employees = frappe.get_all("Employee", filters={"status": "Active"}, fields=["name", "company"])

    for emp in employees:
        # Only consider employees with a salary structure assignment
        if not frappe.db.exists("Salary Structure Assignment", {"employee": emp.name, "docstatus": 1}):
            continue

        # Skip if holiday
        holiday = frappe.get_all("Holiday", filters={"holiday_date": prev_date}, limit_page_length=1)
        if holiday:
            continue

        # Skip if approved leave overlaps
        leave = frappe.get_all(
            "Leave Application",
            filters=[
                ["employee", "=", emp.name],
                ["status", "=", "Approved"],
                ["docstatus", "=", 1],
                ["from_date", "<=", prev_date],
                ["to_date", ">=", prev_date],
            ],
            limit_page_length=1,
        )
        if leave:
            continue

        # Skip if attendance already exists
        existing = frappe.get_all(
            "Attendance", filters={"employee": emp.name, "attendance_date": getdate(prev_date)}, limit_page_length=1
        )
        if existing:
            continue

        # If a submitted Timesheet exists for that day -> mark Present
        ts_exists = frappe.db.exists(
            "Timesheet", {"employee": emp.name, "docstatus": 1, "start_date": prev_date}
        )
        if ts_exists:
            try:
                mark_attendance(emp.name, getdate(prev_date), "Present")
            except Exception:
                frappe.log_error(f"Failed to mark attendance for {emp.name} on {prev_date}")


@frappe.whitelist()
def get_pending_reviews(from_date=None, to_date=None):
    """Return list of employee-date rows that need HR review (no attendance, no approved leave, not holiday).

    If dates are omitted, default to yesterday only.
    """
    if not from_date or not to_date:
        prev = add_days(nowdate(), -1)
        from_date = to_date = prev

    rows = []
    employees = frappe.get_all("Employee", filters={"status": "Active"}, fields=["name", "employee_name", "company"])

    for emp in employees:
        # Only employees with salary structure
        if not frappe.db.exists("Salary Structure Assignment", {"employee": emp.name, "docstatus": 1}):
            continue

        # For each date in range, check conditions
        cur = getdate(from_date)
        end = getdate(to_date)
        while cur <= end:
            # Skip holidays
            if frappe.get_all("Holiday", filters={"holiday_date": cur}, limit_page_length=1):
                cur += timedelta(days=1)
                continue

            # Skip approved leaves
            leave = frappe.get_all(
                "Leave Application",
                filters=[
                    ["employee", "=", emp.name],
                    ["status", "=", "Approved"],
                    ["docstatus", "=", 1],
                    ["from_date", "<=", cur],
                    ["to_date", ">=", cur],
                ],
                limit_page_length=1,
            )
            if leave:
                cur += timedelta(days=1)
                continue

            # If attendance exists or Timesheet exists -> not pending
            att = frappe.get_all("Attendance", filters={"employee": emp.name, "attendance_date": cur}, limit_page_length=1)
            if att:
                cur += timedelta(days=1)
                continue

            ts = frappe.db.exists("Timesheet", {"employee": emp.name, "docstatus": 1, "start_date": cur})
            if not ts:
                rows.append({"employee": emp.name, "employee_name": emp.employee_name, "company": emp.company, "date": cur})

            cur += timedelta(days=1)

    return rows


@frappe.whitelist()
def review_mark(employee: str, date: str, action: str, reason: str = None):
    """Approve (action='accept') -> mark Present; Reject (action='reject') -> mark Absent.

    Requires HR role. When rejecting, `reason` is required.
    """
    _ensure_hr_role()

    if action not in ("accept", "reject"):
        frappe.throw("Invalid action. Use 'accept' or 'reject'.")

    if action == "reject" and not reason:
        frappe.throw("A reason is required when marking Absent.")

    # Do not overwrite existing attendance
    if frappe.get_all("Attendance", filters={"employee": employee, "attendance_date": getdate(date)}, limit_page_length=1):
        frappe.throw("Attendance already exists for this employee and date.")

    if action == "accept":
        mark_attendance(employee, getdate(date), "Present")
    else:
        # create Absent attendance (HR confirmed)
        mark_attendance(employee, getdate(date), "Absent")

    # Log a note for audit
    frappe.get_doc({
        "doctype": "Comment",
        "comment_type": "Info",
        "reference_doctype": "Attendance",
        "content": f"HR review: {action} by {frappe.session.user}; reason: {reason if reason else ''}",
    }).insert(ignore_permissions=True)


@frappe.whitelist()
def review_mark_bulk(data: str | dict):
    """Process bulk review data: list of {employee, date, action, reason}.

    If more than 50 rows, enqueue a background job.
    """
    _ensure_hr_role()

    if isinstance(data, str):
        data = json.loads(data)

    rows = data if isinstance(data, list) else data.get("rows", [])
    if not rows:
        frappe.throw("No rows provided")

    if len(rows) > 50 and not frappe.flags.test_bg_job:
        enqueue(process_bulk_review, queue="long", timeout=600, data=rows)
        return {"status": "queued", "count": len(rows)}

    return process_bulk_review(rows)


def process_bulk_review(rows):
    results = {"processed": 0, "errors": []}
    for r in rows:
        try:
            employee = r.get("employee")
            date = r.get("date")
            action = r.get("action")
            reason = r.get("reason")
            # bypass role check for background job
            if frappe.get_all("Attendance", filters={"employee": employee, "attendance_date": getdate(date)}, limit_page_length=1):
                results["errors"].append({"row": r, "error": "attendance exists"})
                continue
            if action == "accept":
                mark_attendance(employee, getdate(date), "Present")
            elif action == "reject":
                if not reason:
                    results["errors"].append({"row": r, "error": "missing reason"})
                    continue
                mark_attendance(employee, getdate(date), "Absent")
            else:
                results["errors"].append({"row": r, "error": "invalid action"})
                continue
            results["processed"] += 1
        except Exception as e:
            results["errors"].append({"row": r, "error": str(e)})
            frappe.log_error(f"Bulk attendance review failed for {r}: {e}")
            continue
    return results


@frappe.whitelist()
def undo_attendance(employee: str, date: str):
    """Undo attendance by cancelling the Attendance doc for given employee and date.

    Restricted to HR roles.
    """
    _ensure_hr_role()

    att = frappe.get_all("Attendance", filters={"employee": employee, "attendance_date": getdate(date), "docstatus": 1}, limit_page_length=1)
    if not att:
        frappe.throw("No submitted Attendance found to undo.")

    doc = frappe.get_doc("Attendance", att[0].name)
    doc.cancel()
    return {"status": "cancelled", "attendance": att[0].name}
