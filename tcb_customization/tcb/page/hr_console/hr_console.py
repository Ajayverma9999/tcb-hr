import frappe
from frappe.utils import get_first_day, get_last_day, getdate


@frappe.whitelist()
def get_dashboard_data(year, month):
    year = int(year)
    month = int(month)

    start_date = get_first_day(f"{year}-{month:02d}-01")
    end_date = get_last_day(start_date)

    # ---------------------------------------------------------
    # ACTIVE HEADCOUNT
    # Employee was active at some point during selected month.
    # ---------------------------------------------------------
    employees = frappe.get_all(
        "Employee",
        filters={
            "date_of_joining": ["<=", end_date]
        },
        fields=[
            "name",
            "employee_name",
            "status",
            "date_of_joining",
            "relieving_date",
            "department",
            "designation"
        ],
        order_by="employee_name asc",
    )

    active_employees = []

    for employee in employees:
        joining = getdate(employee.date_of_joining) if employee.date_of_joining else None
        relieving = (
            getdate(employee.relieving_date)
            if employee.relieving_date
            else None
        )

        if joining and joining <= end_date:
            if not relieving or relieving >= start_date:
                active_employees.append(employee)

    # ---------------------------------------------------------
    # ATTENDANCE
    # ---------------------------------------------------------
    attendance = frappe.get_all(
        "Attendance",
        filters={
            "attendance_date": ["between", [start_date, end_date]],
            "docstatus": ["<", 2],
        },
        fields=[
            "name",
            "employee",
            "employee_name",
            "attendance_date",
            "status",
            "department"
        ],
        order_by="attendance_date desc, employee_name asc",
    )

    present = []
    absent = []
    on_leave = []
    work_from_home = []

    # Keep employee/date combination unique.
    present_seen = set()
    absent_seen = set()
    leave_seen = set()
    wfh_seen = set()

    for row in attendance:
        key = row.employee

        if row.status == "Present" and key not in present_seen:
            present.append(row)
            present_seen.add(key)

        elif row.status == "Absent" and key not in absent_seen:
            absent.append(row)
            absent_seen.add(key)

        elif row.status == "On Leave" and key not in leave_seen:
            on_leave.append(row)
            leave_seen.add(key)

        elif row.status == "Work From Home" and key not in wfh_seen:
            work_from_home.append(row)
            wfh_seen.add(key)

    # ---------------------------------------------------------
    # DRAFT TIMESHEETS
    # ---------------------------------------------------------
    draft_timesheets = frappe.get_all(
        "Timesheet",
        filters={
            "docstatus": 0,
            "start_date": ["between", [start_date, end_date]],
        },
        fields=[
            "name",
            "employee",
            "employee_name",
            "start_date",
            "total_hours"
        ],
        order_by="start_date desc, modified desc",
    )

    # ---------------------------------------------------------
    # EXPENSE CLAIMS
    # ---------------------------------------------------------

    expense_claims = frappe.get_all(
        "Expense Claim",
        filters={
            "posting_date": ["between", [start_date, end_date]],
            "approval_status": "Draft",
        },
        fields=[
            "name",
            "employee",
            "employee_name",
            "posting_date",
            "total_claimed_amount",
            "total_sanctioned_amount",
            "approval_status",
        ],
        order_by="posting_date desc, modified desc",
    )

    # ---------------------------------------------------------
    # LEAVE APPLICATIONS
    # ---------------------------------------------------------

    leave_applications = frappe.get_all(
        "Leave Application",
        filters={
            "from_date": ["<=", end_date],
            "to_date": [">=", start_date],
            "status": "Open",
        },
        fields=[
            "name",
            "employee",
            "employee_name",
            "leave_type",
            "from_date",
            "to_date",
            "status",
            "total_leave_days",
        ],
        order_by="from_date desc, modified desc",
    )

    return {
        "period": {
            "year": year,
            "month": month,
            "start_date": str(start_date),
            "end_date": str(end_date),
        },
        "counts": {
            "active": len(active_employees),
            "present": len(present),
            "absent": len(absent),
            "pending": len(draft_timesheets),
            "on_leave": len(on_leave),
            "work_from_home": len(work_from_home),
            "leave_applications": len(leave_applications),
            "expense_claims": len(expense_claims),
        },
        "employees": {
            "active": active_employees,
            "present": present,
            "absent": absent,
            "on_leave": on_leave,
            "work_from_home": work_from_home,
        },

        "leave_applications": leave_applications,

        "expense_claims": expense_claims,

        "timesheets": draft_timesheets,
    }
