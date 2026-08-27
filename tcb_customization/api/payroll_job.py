import frappe
from frappe.utils import add_months, get_first_day, get_last_day, nowdate, getdate
from hrms.payroll.doctype.payroll_entry.payroll_entry import PayrollEntry


def create_monthly_payroll_draft():
    """Create a draft Payroll Entry + draft Salary Slips for previous calendar month for each company.

    If pending attendance reviews exist for the period, create the draft but add a comment/warning.
    """
    prev = add_months(nowdate(), -1)
    start_date = get_first_day(prev)
    end_date = get_last_day(prev)

    # Check HR Settings for auto-create and lock day
    try:
        hr = frappe.get_single('HR Settings')
        auto_create = bool(hr.get('payroll_auto_create_draft'))
        lock_day = hr.get('payroll_lock_day')
    except Exception:
        auto_create = True
        lock_day = None

    if not auto_create:
        return

    # If a payroll_lock_day is configured, only run on that day of month
    if lock_day:
        today_day = getdate(nowdate()).day
        try:
            if int(lock_day) != int(today_day):
                return
        except Exception:
            # if lock_day invalid, ignore and proceed
            pass

    companies = frappe.get_all("Company", fields=["name", "default_currency", "default_payable_account"])

    for c in companies:
        # Skip if payroll entry already exists for company and period
        exists = frappe.get_all(
            "Payroll Entry",
            filters={"company": c.name, "start_date": start_date, "end_date": end_date, "docstatus": ["!=", 2]},
            limit_page_length=1,
        )
        if exists:
            continue

        currency = c.default_currency or frappe.get_value("Company", c.name, "default_currency")
        payroll_payable = c.default_payable_account or frappe.get_value("Company", c.name, "default_payable_account")
        if not payroll_payable:
            frappe.log_error(f"No default payable account set for Company {c.name}. Skipping payroll draft.")
            continue

        pe = frappe.get_doc(
            {
                "doctype": "Payroll Entry",
                "posting_date": nowdate(),
                "company": c.name,
                "currency": currency,
                "exchange_rate": 1,
                "payroll_payable_account": payroll_payable,
                "start_date": start_date,
                "end_date": end_date,
                "payroll_frequency": "Monthly",
                "salary_slip_based_on_timesheet": 1,
            }
        )

        try:
            pe.insert(ignore_permissions=True)
            # Fill employees and create draft salary slips
            try:
                pe.fill_employee_details()
            except Exception:
                # ignore if filters don't match any employees
                pass

            # Create salary slips in draft
            try:
                pe.create_salary_slips()
            except Exception as e:
                frappe.log_error(f"Failed to create salary slips for Payroll Entry {pe.name}: {e}")

            # Warn if there are pending attendance reviews
            pending = frappe.get_attr("tcb_customization.api.attendance_job.get_pending_reviews")()
            if pending:
                frappe.get_doc({
                    "doctype": "Comment",
                    "comment_type": "Info",
                    "reference_doctype": "Payroll Entry",
                    "reference_name": pe.name,
                    "content": f"Warning: {len(pending)} attendance review(s) unresolved for this period.",
                }).insert(ignore_permissions=True)

        except Exception as e:
            frappe.log_error(f"Failed to create payroll draft for company {c.name}: {e}")


def on_payroll_submit(doc, method=None):
    """Hook: run when Payroll Entry is submitted. Currently adds an audit comment.

    Attendance and Leave edits are prevented by `prevent_edit_if_locked` which checks for submitted Payroll Entry.
    """
    frappe.get_doc(
        {
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": "Payroll Entry",
            "reference_name": doc.name,
            "content": f"Payroll submitted by {frappe.session.user} on {nowdate()}",
        }
    ).insert(ignore_permissions=True)


def prevent_edit_if_locked(doc, method=None):
    """Prevent editing Attendance or Leave Application if a submitted Payroll Entry covers the date."""
    # Determine date to check
    if doc.doctype == "Attendance":
        date = getdate(doc.attendance_date)
        employee = doc.employee
    else:
        # Leave Application
        date = getdate(doc.from_date) if doc.from_date == doc.to_date else None
        # For multi-day leave, check the date range
        employee = doc.employee

    if not employee:
        return

    company = frappe.get_value("Employee", employee, "company")
    if not company:
        return

    # Build filter to find any submitted Payroll Entry covering the date (or range)
    filters = {"company": company, "docstatus": 1}
    entries = frappe.get_all(
        "Payroll Entry",
        filters=filters,
        fields=["name", "start_date", "end_date"],
    )
    from datetime import date as dt_date

    for e in entries:
        start = getdate(e.start_date)
        end = getdate(e.end_date)
        if doc.doctype == "Attendance":
            if start <= getdate(doc.attendance_date) <= end:
                frappe.throw("Cannot modify Attendance because payroll for this period has been submitted.")
        else:
            # Leave Application: if any overlap between leave range and payroll period
            leave_from = getdate(doc.from_date)
            leave_to = getdate(doc.to_date)
            if (leave_from <= end) and (leave_to >= start):
                frappe.throw("Cannot modify Leave Application because payroll for this period has been submitted.")
