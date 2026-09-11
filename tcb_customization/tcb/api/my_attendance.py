import calendar

import frappe
from frappe.utils import add_days, get_first_day, get_last_day, getdate, today


@frappe.whitelist()
def get_my_attendance(year=None, month=None):
    employee = get_logged_in_employee()

    year = int(year or getdate(today()).year)
    month = int(month or getdate(today()).month)

    start_date = get_first_day(getdate(f"{year}-{month:02d}-01"))
    end_date = get_last_day(start_date)

    employee_data = frappe.db.get_value(
        "Employee",
        employee,
        [
            "employee_name",
            "department",
            "designation",
            "name",
        ],
        as_dict=True,
    )

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
            "leave_type",
            "from_date",
            "to_date",
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

        calendar_data.append({
            "date": date_key,
            "day": day,
            "status": status,
            "leave_type": leave_type,
            "short_code": short_code,
            "working_hours": working_hours,
        })

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


def get_logged_in_employee():
    if frappe.session.user == "Guest":
        frappe.throw(
            "Please login to view your attendance."
        )

    employee = frappe.db.get_value(
        "Employee",
        {
            "user_id": frappe.session.user,
            "status": "Active",
        },
        "name",
    )

    if not employee:
        frappe.throw(
            "No active Employee is linked with your login user."
        )

    return employee


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
        fields=["name"],
        order_by="name asc",
    )

    balances = []

    for leave_type in leave_types:
        allocations = frappe.get_all(
            "Leave Allocation",
            filters={
                "employee": employee,
                "leave_type": leave_type.name,
                "docstatus": 1,
                "from_date": ["<=", as_on],
                "to_date": [">=", as_on],
            },
            fields=[
                "name",
                "total_leaves_allocated",
                "from_date",
                "to_date",
            ],
        )

        allocated = sum(
            float(row.total_leaves_allocated or 0)
            for row in allocations
        )

        approved_leaves = frappe.get_all(
            "Leave Application",
            filters={
                "employee": employee,
                "leave_type": leave_type.name,
                "status": "Approved",
                "docstatus": 1,
                "from_date": ["<=", as_on],
            },
            fields=[
                "from_date",
                "to_date",
                "total_leave_days",
            ],
        )

        taken = 0

        for leave in approved_leaves:
            leave_from = getdate(leave.from_date)
            leave_to = getdate(leave.to_date)

            if leave_from <= getdate(as_on):
                effective_to = min(
                    leave_to,
                    getdate(as_on),
                )

                if effective_to >= leave_from:
                    taken += float(
                        leave.total_leave_days or 0
                    )

        balance = max(allocated - taken, 0)

        balances.append({
            "leave_type": leave_type.name,
            "short_code": get_leave_short_code(
                leave_type.name
            ),
            "balance": balance,
        })

    return balances
