import frappe
from frappe.utils import add_months, get_first_day, get_last_day, getdate, today
from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip


def create_monthly_salary_slips():
    """
    Create previous month's Salary Slips for all active employees.

    Runs on the 28th of every month.

    Salary Slips:
    - Draft status
    - Based on submitted Salary Structure Assignment
    - Approved Expense Claims are added as Expense Reimbursement
    - Duplicate Salary Slips are skipped
    """

    run_date = getdate(today())

    # Previous month
    payroll_date = add_months(run_date, -1)

    start_date = get_first_day(payroll_date)
    end_date = get_last_day(payroll_date)

    employees = frappe.get_all(
        "Employee",
        filters={
            "status": "Active",
            "company": "tcb",
            "date_of_joining": ["<=", end_date],
        },
        fields=[
            "name",
            "employee_name",
            "company",
            "date_of_joining",
            "relieving_date",
        ],
    )

    created = []
    skipped = []
    errors = []

    for employee in employees:

        # Employee should have been employed during payroll month
        if employee.relieving_date and getdate(employee.relieving_date) < start_date:
            continue

        try:
            # ---------------------------------------------------------
            # DUPLICATE CHECK
            # ---------------------------------------------------------
            existing = frappe.db.exists(
                "Salary Slip",
                {
                    "employee": employee.name,
                    "start_date": start_date,
                    "end_date": end_date,
                    "docstatus": ["!=", 2],
                },
            )

            if existing:
                skipped.append(
                    {
                        "employee": employee.name,
                        "salary_slip": existing,
                        "reason": "Salary Slip already exists",
                    }
                )
                continue

            # ---------------------------------------------------------
            # CREATE SALARY SLIP FROM SALARY STRUCTURE
            # ---------------------------------------------------------
            slip = make_salary_slip(
                "Standard Monthly Salary",
                employee=employee.name,
                posting_date=end_date,

            )

            # Make sure payroll dates are previous month
            slip.start_date = start_date
            slip.end_date = end_date
            slip.posting_date = end_date

            # Fix Salary Slip naming series after employee is known
            slip.default_series = f"Sal Slip/{employee.name}/.#####"
            slip.name = None
            slip.autoname()

            # APPROVED EXPENSE CLAIMS
            # ---------------------------------------------------------
            claims = frappe.get_all(
                "Expense Claim",
                filters={
                    "employee": employee.name,
                    "approval_status": "Approved",
                    "posting_date": ["between", [start_date, end_date]],
                },
                fields=[
                    "name",
                    "total_sanctioned_amount",
                    "total_amount_reimbursed",
                ],
            )

            expense_total = 0

            for claim in claims:
                sanctioned = float(claim.total_sanctioned_amount or 0)
                reimbursed = float(claim.total_amount_reimbursed or 0)

                # Only unreimbursed approved amount
                pending_reimbursement = max(sanctioned - reimbursed, 0)

                expense_total += pending_reimbursement

            # ---------------------------------------------------------
            # ADD EXPENSE REIMBURSEMENT
            # ---------------------------------------------------------
            if expense_total > 0:
                slip.append(
                    "earnings",
                    {
                        "salary_component": "Expense Reimbursement",
                        "amount": expense_total,
                    },
                )

                # Recalculate salary totals
                slip.calculate_net_pay()

            # ---------------------------------------------------------
            # INSERT AS DRAFT
            # ---------------------------------------------------------
            slip.insert(ignore_permissions=True)

            created.append(
                {
                    "employee": employee.name,
                    "employee_name": employee.employee_name,
                    "salary_slip": slip.name,
                    "expense_reimbursement": expense_total,
                    "gross_pay": slip.gross_pay,
                    "net_pay": slip.net_pay,
                }
            )

            frappe.db.commit()

        except Exception:
            frappe.db.rollback()

            errors.append(
                {
                    "employee": employee.name,
                    "employee_name": employee.employee_name,
                    "error": frappe.get_traceback(),
                }
            )

    # -------------------------------------------------------------
    # HR MANAGER REMINDER
    # -------------------------------------------------------------
    if created:
        notify_hr_managers(
            start_date=start_date,
            end_date=end_date,
            created_count=len(created),
        )

    return {
        "payroll_period": f"{start_date} to {end_date}",
        "created": created,
        "skipped": skipped,
        "errors": errors,
    }


def notify_hr_managers(start_date, end_date, created_count):
    """
    Send in-app Notification Log to users having HR Manager role.
    """

    hr_managers = frappe.get_all(
        "Has Role",
        filters={
            "role": "HR Manager",
        },
        fields=["parent"],
    )

    sent_to = set()

    for row in hr_managers:

        user = row.parent

        # Only actual User records
        if not frappe.db.exists("User", user):
            continue

        if user in sent_to:
            continue

        # Don't notify disabled users
        if frappe.db.get_value("User", user, "enabled") == 0:
            continue

        try:
            notification = frappe.get_doc(
                {
                    "doctype": "Notification Log",
                    "for_user": user,
                    "type": "Alert",
                    "document_type": "Salary Slip",
                    "subject": "Monthly Salary Slips Available",
                    "email_content": (
                        "All employees' salary slips are available in Draft status. "
                        "Please review and submit them."
                    ),
                }
            )

            notification.insert(ignore_permissions=True)
            sent_to.add(user)

        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                "HR Manager Salary Slip Notification Error",
            )

    frappe.db.commit()
