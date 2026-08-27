import frappe
from frappe import _
from frappe.utils import getdate


def _ensure_hr_or_system_manager():
    if not (("HR Manager" in frappe.get_roles()) or ("System Manager" in frappe.get_roles())):
        frappe.throw(_("You are not permitted to access this resource."), frappe.PermissionError)


@frappe.whitelist()
def get_overview(from_date=None, to_date=None):
    """Return basic HR dashboard numbers: headcount and pending attendance reviews."""
    _ensure_hr_or_system_manager()

    headcount = frappe.db.count("Employee", {"status": "Active"})

    # reuse attendance job utility if available
    pending = []
    try:
        from tcb_customization.api import attendance_job

        pending = attendance_job.get_pending_reviews(from_date=from_date, to_date=to_date)
    except Exception:
        pending = []

    return {
        "headcount": headcount,
        "pending_attendance_reviews": len(pending),
    }


@frappe.whitelist()
def get_employee_list(start=0, limit=50, search=None, department=None):
    _ensure_hr_or_system_manager()
    try:
        start = int(start)
    except (TypeError, ValueError):
        start = 0
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 50

    filters = [["status", "=", "Active"]]
    if department:
        filters.append(["department", "=", department])

    if search:
        like = f"%{search}%"
        filters.append(["or", ["employee_name", "like", like], ["name", "like", like]])

    employees = frappe.get_all(
        "Employee",
        filters=filters,
        fields=["name", "employee_name", "department", "designation"],
        limit_page_length=limit,
        order_by="employee_name asc",
        offset=start,
    )
    return employees


@frappe.whitelist()
def get_departments():
    _ensure_hr_or_system_manager()
    rows = frappe.db.sql(
        """
        SELECT DISTINCT department FROM `tabEmployee`
        WHERE department IS NOT NULL AND department != '' AND status='Active'
        ORDER BY department
        """,
        as_dict=False,
    )
    # sql returns list of tuples
    return [r[0] for r in rows]


@frappe.whitelist()
def get_companies():
    _ensure_hr_or_system_manager()
    rows = frappe.db.sql(
        """
        SELECT DISTINCT company FROM `tabEmployee`
        WHERE company IS NOT NULL AND company != '' AND status='Active'
        ORDER BY company
        """,
        as_dict=False,
    )
    return [r[0] for r in rows]


@frappe.whitelist()
def get_employee_detail(employee, from_date, to_date):
    _ensure_hr_or_system_manager()
    from_date = getdate(from_date)
    to_date = getdate(to_date)

    attendance = frappe.get_all(
        "Attendance",
        filters={"employee": employee, "attendance_date": ["between", [from_date, to_date]]},
        fields=["attendance_date", "status", "name"],
        order_by="attendance_date asc",
    )

    salary_slips = frappe.get_all(
        "Salary Slip",
        filters={"employee": employee, "start_date": ["< =", to_date], "end_date": [">=", from_date]},
        fields=["name", "start_date", "end_date", "net_pay"],
        order_by="start_date desc",
    )

    return {"attendance": attendance, "salary_slips": salary_slips}


@frappe.whitelist()
def get_pending_reviews(from_date=None, to_date=None):
    _ensure_hr_or_system_manager()
    try:
        from tcb_customization.api import attendance_job
        rows = attendance_job.get_pending_reviews(from_date=from_date, to_date=to_date)
        return rows
    except Exception as e:
        frappe.log_error(f"Failed to fetch pending reviews: {e}")
        return []


@frappe.whitelist()
def bulk_review(data):
    """Proxy to attendance_job.review_mark_bulk for HR Console bulk actions."""
    _ensure_hr_or_system_manager()
    try:
        from tcb_customization.api import attendance_job
        return attendance_job.review_mark_bulk(data)
    except Exception as e:
        frappe.log_error(f"Bulk review proxy failed: {e}")
        frappe.throw("Bulk review failed; check error logs.")
