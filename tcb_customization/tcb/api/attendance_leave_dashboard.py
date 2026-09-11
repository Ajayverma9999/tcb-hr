import calendar

import frappe
from frappe.utils import add_days, get_first_day, get_last_day, getdate, today


@frappe.whitelist()
def get_employees():
    if not has_hr_access():
        frappe.throw("Not permitted", frappe.PermissionError)

    return frappe.get_all(
        "Employee",
        filters={
            "status": "Active",
            "company": "tcb",
        },
        fields=["name", "employee_name"],
        order_by="employee_name asc",
    )


@frappe.whitelist()
def get_dashboard_data(employee, year=None, month=None):
    if not has_hr_access():
        frappe.throw("Not permitted", frappe.PermissionError)

    if not employee:
        frappe.throw("Employee is required")

    year = int(year or getdate(today()).year)
    month = int(month or getdate(today()).month)

    start_date = get_first_day(getdate(f"{year}-{month:02d}-01"))
    end_date = get_last_day(start_date)

    employee_data = frappe.db.get_value(
        "Employee",
        employee,
        ["employee_name", "department", "designation"],
        as_dict=True,
    )

    if not employee_data:
        frappe.throw("Employee not found")

    attendance = frappe.get_all(
        "Attendance",
        filters={
            "employee": employee,
            "attendance_date": ["between", [start_date, end_date]],
            "docstatus": 1,
        },
        fields=[
            "attendance_date",
            "status",
            "working_hours",
            "leave_type",
        ],
    )

    attendance_map = {
        str(row.attendance_date): row
        for row in attendance
    }

    leaves = frappe.get_all(
        "Leave Application",
        filters={
            "employee": employee,
            "status": "Approved",
            "from_date": ["<=", end_date],
            "to_date": [">=", start_date],
            "docstatus": 1,
        },
        fields=[
            "name",
            "leave_type",
            "from_date",
            "to_date",
            "total_leave_days",
        ],
    )

    leave_map = {}

    for leave in leaves:
        current = max(
            getdate(leave.from_date),
            getdate(start_date),
        )

        last = min(
            getdate(leave.to_date),
            getdate(end_date),
        )

        while current <= last:
            leave_map[str(current)] = {
                "leave_type": leave.leave_type,
                "short_code": get_leave_short_code(
                    leave.leave_type
                ),
            }

            current = add_days(current, 1)

    calendar_data = []

    days_in_month = calendar.monthrange(year, month)[1]

    for day in range(1, days_in_month + 1):
        date_value = getdate(
            f"{year}-{month:02d}-{day:02d}"
        )

        date_key = str(date_value)

        status = None
        leave_type = None
        short_code = None
        working_hours = None

        if date_key in leave_map:
            status = "Leave"
            leave_type = leave_map[date_key]["leave_type"]
            short_code = leave_map[date_key]["short_code"]

        elif date_key in attendance_map:
            row = attendance_map[date_key]

            status = row.status
            leave_type = row.leave_type
            working_hours = row.working_hours

            if leave_type:
                short_code = get_leave_short_code(
                    leave_type
                )

        calendar_data.append(
            {
                "date": date_key,
                "day": day,
                "status": status,
                "leave_type": leave_type,
                "short_code": short_code,
                "working_hours": working_hours,
            }
        )

    return {
        "employee": employee,
        "employee_name": employee_data.employee_name,
        "department": employee_data.department,
        "designation": employee_data.designation,
        "year": year,
        "month": month,
        "month_name": calendar.month_name[month],
        "calendar": calendar_data,
        "leave_balance": get_leave_balance(
            employee,
            end_date,
        ),
    }


def get_leave_short_code(leave_type):
    if not leave_type:
        return None

    text = leave_type.lower().strip()

    if "casual" in text:
        return "CL"

    if "sick" in text:
        return "SL"

    if (
        "without pay" in text
        or "unpaid" in text
        or text == "lwp"
    ):
        return "LWP"

    if "earned" in text:
        return "EL"

    if "privilege" in text:
        return "PL"

    if "medical" in text:
        return "ML"

    words = leave_type.split()

    if len(words) >= 2:
        return "".join(
            word[0].upper()
            for word in words[:2]
        )

    return leave_type[:3].upper()


def get_leave_balance(employee, as_on):
    leave_types = frappe.get_all(
        "Leave Type",
        filters={
            "is_active": 1,
        },
        fields=["name"],
        order_by="name asc",
    )

    balances = []

    for leave_type in leave_types:
        balance = frappe.db.sql(
            """
            SELECT
                COALESCE(SUM(total_leaves_allocated), 0)
                - COALESCE(SUM(leaves_taken), 0)
            FROM `tabLeave Allocation`
            WHERE employee = %s
              AND leave_type = %s
              AND docstatus = 1
              AND from_date <= %s
              AND to_date >= %s
            """,
            (
                employee,
                leave_type.name,
                as_on,
                as_on,
            ),
        )[0][0] or 0

        balances.append(
            {
                "leave_type": leave_type.name,
                "short_code": get_leave_short_code(
                    leave_type.name
                ),
                "balance": float(balance),
            }
        )

    return balances


def has_hr_access():
    if frappe.session.user == "Administrator":
        return True

    roles = set(
        frappe.get_roles(frappe.session.user)
    )

    return bool(
        roles.intersection(
            {
                "HR Manager",
                "HR User",
                "System Manager",
            }
        )
    )
