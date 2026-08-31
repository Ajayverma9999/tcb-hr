import frappe
from frappe import _
from frappe.utils import getdate, today, add_days


def _ensure_hr_or_system_manager():
    if not (
        "HR Manager" in frappe.get_roles()
        or "System Manager" in frappe.get_roles()
    ):
        frappe.throw(
            _("You are not permitted to access this resource."),
            frappe.PermissionError,
        )


def _get_attendance_status_map(attendance_date):
    rows = frappe.get_all(
        "Attendance",
        filters={
            "attendance_date": attendance_date,
        },
        fields=[
            "employee",
            "status",
        ],
    )

    return {
        row.employee: row.status
        for row in rows
    }


def _get_on_leave_employees(attendance_date):
    rows = frappe.db.sql(
        """
        SELECT DISTINCT employee
        FROM `tabLeave Application`
        WHERE status = 'Approved'
          AND from_date <= %s
          AND to_date >= %s
        """,
        (attendance_date, attendance_date),
        as_dict=True,
    )

    return {row.employee for row in rows}


def _get_active_employees(attendance_date, department=None, search=None):
    """
    Return employees who were active on the selected date.

    The Employee DocType in this installation does not have
    a date_of_leaving field, so eligibility is based on
    date_of_joining only.
    """

    filters = {
        "date_of_joining": ["<=", attendance_date],
    }

    if department:
        filters["department"] = department

    if search:
        search_like = f"%{search}%"

        return frappe.get_all(
            "Employee",
            filters=filters,
            or_filters=[
                ["employee_name", "like", search_like],
                ["name", "like", search_like],
            ],
            fields=[
                "name",
                "employee_name",
                "department",
                "designation",
                "company",
                "date_of_joining",
            ],
            order_by="employee_name asc",
        )

    return frappe.get_all(
        "Employee",
        filters=filters,
        fields=[
            "name",
            "employee_name",
            "department",
            "designation",
            "company",
            "date_of_joining",
        ],
        order_by="employee_name asc",
    )


def _get_employee_status(employee_id, attendance_status, on_leave_employees):
    """
    Attendance status priority:

    1. Approved Leave
    2. Attendance status
    3. Pending
    """

    if employee_id in on_leave_employees:
        return "On Leave"

    status = attendance_status.get(employee_id)

    if status:
        return status

    return "Pending"


@frappe.whitelist()
def get_overview(from_date=None, to_date=None, attendance_date=None):
    """
    HR Console overview.

    The cards represent the employee attendance snapshot
    for the selected To Date.

    From Date -> To Date is used for the selected period,
    while dashboard card counts are mutually exclusive
    for the To Date.
    """

    _ensure_hr_or_system_manager()

    # Backward compatibility with old single-date calls
    if not from_date:
        from_date = attendance_date or today()

    if not to_date:
        to_date = from_date

    from_date = getdate(from_date)
    to_date = getdate(to_date)

    if from_date > to_date:
        frappe.throw("From Date cannot be greater than To Date.")

    # Employee population active on the selected To Date
    active_employees = _get_active_employees(
        attendance_date=to_date
    )

    attendance_status = _get_attendance_status_map(
        to_date
    )

    on_leave_employees = _get_on_leave_employees(
        to_date
    )

    present_count = 0
    absent_count = 0
    pending_count = 0
    leave_count = 0

    # Each employee belongs to exactly ONE card.
    for employee in active_employees:

        employee_id = employee.name

        status = _get_employee_status(
            employee_id,
            attendance_status,
            on_leave_employees,
        )

        if status == "Present":
            present_count += 1

        elif status == "Absent":
            absent_count += 1

        elif status == "On Leave":
            leave_count += 1

        else:
            pending_count += 1

    return {
        "from_date": str(from_date),
        "to_date": str(to_date),

        "headcount": len(active_employees),

        "present": present_count,
        "present_today": present_count,

        "absent": absent_count,

        "pending": pending_count,
        "pending_attendance": pending_count,

        "on_leave": leave_count,
        "on_leave_today": leave_count,

        # Kept for frontend backward compatibility
        "pending_attendance_reviews": pending_count,
    }


@frappe.whitelist()
def get_attendance_employees(
    attendance_date=None,
    from_date=None,
    to_date=None,
    status=None,
    start=0,
    limit=50,
    search=None,
    department=None,
):
    """
    Return employees according to attendance status
    for a selected date range.

    Supported statuses:
        All
        Active
        Present
        Absent
        Pending
        On Leave
    """

    _ensure_hr_or_system_manager()

    # Backward compatibility
    if not from_date:
        from_date = attendance_date or today()

    if not to_date:
        to_date = from_date

    from_date = getdate(from_date)
    to_date = getdate(to_date)

    if from_date > to_date:
        frappe.throw("From Date cannot be greater than To Date.")

    try:
        start = int(start)
    except (TypeError, ValueError):
        start = 0

    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 50

    status = status or "Active"

    employees = _get_active_employees(
        attendance_date=to_date,
        department=department,
        search=search,
    )

    result = []

    current_date = from_date

    # Employee status history inside selected range
    employee_statuses = {
        employee.name: set()
        for employee in employees
    }

    while current_date <= to_date:

        attendance_status = _get_attendance_status_map(
            current_date
        )

        on_leave_employees = _get_on_leave_employees(
            current_date
        )

        for employee in employees:

            employee_id = employee.name

            if employee.date_of_joining:
                if getdate(employee.date_of_joining) > current_date:
                    continue

            employee_status = _get_employee_status(
                employee_id,
                attendance_status,
                on_leave_employees,
            )

            employee_statuses[employee_id].add(
                employee_status
            )

        current_date = add_days(current_date, 1)

    for employee in employees:

        employee_id = employee.name

        statuses = employee_statuses.get(
            employee_id,
            set()
        )

        if status == "Active":
            include = True

        elif status == "Present":
            include = "Present" in statuses

        elif status == "Absent":
            include = "Absent" in statuses

        elif status == "Pending":
            include = "Pending" in statuses

        elif status == "On Leave":
            include = "On Leave" in statuses

        elif status == "All":
            include = True

        else:
            include = False

        if not include:
            continue

        employee["attendance_status"] = (
            status if status != "Active"
            else "Active"
        )

        employee["from_date"] = str(from_date)
        employee["to_date"] = str(to_date)

        result.append(employee)

    return result[start:start + limit]


@frappe.whitelist()
def get_employee_list(
    start=0,
    limit=50,
    search=None,
    department=None,
):
    """
    Return currently active employees.
    """

    _ensure_hr_or_system_manager()

    try:
        start = int(start)
    except (TypeError, ValueError):
        start = 0

    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 50

    employees = _get_active_employees(
        attendance_date=getdate(today()),
        department=department,
        search=search,
    )

    return employees[start:start + limit]

@frappe.whitelist()
def get_departments():

    _ensure_hr_or_system_manager()

    rows = frappe.db.sql(
        """
        SELECT DISTINCT department
        FROM `tabEmployee`
        WHERE department IS NOT NULL
          AND department != ''
        ORDER BY department
        """,
        as_dict=False,
    )

    return [
        row[0]
        for row in rows
    ]


@frappe.whitelist()
def get_companies():

    _ensure_hr_or_system_manager()

    rows = frappe.db.sql(
        """
        SELECT DISTINCT company
        FROM `tabEmployee`
        WHERE company IS NOT NULL
          AND company != ''
        ORDER BY company
        """,
        as_dict=False,
    )

    return [
        row[0]
        for row in rows
    ]


@frappe.whitelist()
def get_employee_detail(
    employee,
    from_date,
    to_date,
):

    _ensure_hr_or_system_manager()

    from_date = getdate(from_date)
    to_date = getdate(to_date)

    employee_doc = frappe.db.get_value(
        "Employee",
        employee,
        [
            "name",
            "employee_name",
            "department",
            "designation",
            "company",
            "date_of_joining",
            "cell_number",
            "personal_email",
            "user_id",
        ],
        as_dict=True,
    )

    attendance = frappe.get_all(
        "Attendance",
        filters={
            "employee": employee,
            "attendance_date": [
                "between",
                [
                    from_date,
                    to_date,
                ],
            ],
        },
        fields=[
            "attendance_date",
            "status",
            "name",
            "working_hours",
            "in_time",
            "out_time",
        ],
        order_by="attendance_date asc",
    )

    salary_slips = frappe.get_all(
        "Salary Slip",
        filters={
            "employee": employee,
            "start_date": [
                "<=",
                to_date,
            ],
            "end_date": [
                ">=",
                from_date,
            ],
        },
        fields=[
            "name",
            "start_date",
            "end_date",
            "total_working_days",
            "payment_days",
            "leave_without_pay",
            "absent_days",
            "gross_pay",
            "total_deduction",
            "net_pay",
        ],
        order_by="start_date desc",
    )

    return {
        "employee": employee_doc,
        "attendance": attendance,
        "salary_slips": salary_slips,
        "from_date": str(from_date),
        "to_date": str(to_date),
    }


@frappe.whitelist()
def get_pending_reviews(
    from_date=None,
    to_date=None,
):

    _ensure_hr_or_system_manager()

    try:

        from tcb_customization.api import attendance_job

        rows = attendance_job.get_pending_reviews(
            from_date=from_date,
            to_date=to_date,
        )

        return rows

    except Exception as e:

        frappe.log_error(
            f"Failed to fetch pending reviews: {e}"
        )

        return []


@frappe.whitelist()
def bulk_review(data):
    """
    Proxy to attendance_job.review_mark_bulk
    for HR Console bulk actions.
    """

    _ensure_hr_or_system_manager()

    try:

        from tcb_customization.api import attendance_job

        return attendance_job.review_mark_bulk(
            data
        )

    except Exception as e:

        frappe.log_error(
            f"Bulk review proxy failed: {e}"
        )

        frappe.throw(
            "Bulk review failed; check error logs."
        )


@frappe.whitelist()
def get_pending_timesheets(
    employee=None,
    from_date=None,
    to_date=None,
    search=None,
):
    """
    Return draft/pending Timesheets for HR review.

    Pending Timesheet = Timesheet with docstatus = 0
    inside the selected date range.
    """

    _ensure_hr_or_system_manager()

    from_date = getdate(from_date or today())
    to_date = getdate(to_date or today())

    filters = [
        ["docstatus", "=", 0],
        ["start_date", "<=", to_date],
        ["end_date", ">=", from_date],
    ]

    if employee:
        filters.append(
            ["employee", "=", employee]
        )

    if search:
        employees = frappe.get_all(
            "Employee",
            filters={
                "status": "Active",
            },
            or_filters=[
                ["employee_name", "like", f"%{search}%"],
                ["name", "like", f"%{search}%"],
            ],
            pluck="name",
        )

        if not employees:
            return []

        filters.append(
            ["employee", "in", employees]
        )

    timesheets = frappe.get_all(
        "Timesheet",
        filters=filters,
        fields=[
            "name",
            "employee",
            "employee_name",
            "start_date",
            "end_date",
            "total_hours",
            "status",
        ],
        order_by="start_date desc, modified desc",
    )

    for row in timesheets:
        row["time_logs"] = frappe.get_all(
            "Timesheet Detail",
            filters={
                "parent": row.name,
                "parenttype": "Timesheet",
            },
            fields=[
                "activity_type",
                "from_time",
                "to_time",
                "hours",
                "description",
                "project",
                "task",
            ],
            order_by="idx asc",
        )

    return timesheets


@frappe.whitelist()
def review_pending_timesheet(
    timesheet,
    action,
    reason=None,
):
    """
    HR action on a pending Timesheet.

    approve:
        Submit the Timesheet.

    reject:
        Keep it as draft and add an audit comment.
    """

    _ensure_hr_or_system_manager()

    if action not in ("approve", "reject"):
        frappe.throw(
            _("Invalid action. Use approve or reject.")
        )

    if action == "reject" and not reason:
        frappe.throw(
            _("Reason is required when rejecting a Timesheet.")
        )

    doc = frappe.get_doc(
        "Timesheet",
        timesheet,
    )

    if doc.docstatus != 0:
        frappe.throw(
            _("This Timesheet is no longer pending.")
        )

    if action == "approve":
        doc.submit()

        return {
            "status": "approved",
            "timesheet": doc.name,
        }

    frappe.get_doc({
        "doctype": "Comment",
        "comment_type": "Info",
        "reference_doctype": "Timesheet",
        "reference_name": doc.name,
        "content": (
            f"HR Timesheet rejected by "
            f"{frappe.session.user}. "
            f"Reason: {reason}"
        ),
    }).insert(ignore_permissions=True)

    return {
        "status": "rejected",
        "timesheet": doc.name,
    }
