import frappe
from frappe import _


def _ensure_hr_role():
    if not (("HR Manager" in frappe.get_roles()) or ("System Manager" in frappe.get_roles())):
        frappe.throw("Only HR Manager or System Manager can perform this action.", frappe.PermissionError)


def create_additional_salary_for_expense(doc, method):
    """Hook: when an Expense Claim is submitted, create an Additional Salary for reimbursement.

    This function creates a Draft Additional Salary linked to the employee and expense claim.
    It will not submit; HR can review and include it in payroll.
    """
    # Only act when submitted (docstatus==1)
    if doc.docstatus != 1:
        return

    # Only process approved expense claims
    if doc.status not in ("Approved", "Paid") and not getattr(doc, 'workflow_state', None) == 'Approved':
        return

    # Find employee
    employee = doc.employee or frappe.get_value("Employee", {"user_id": doc.owner}, "name")
    if not employee:
        frappe.log_error("Expense Claim has no linked Employee: {0}".format(doc.name))
        return

    # Create Additional Salary
    try:
        add = frappe.get_doc({
            "doctype": "Additional Salary",
            "employee": employee,
            "company": doc.company,
            "salary_component": frappe.get_value("Salary Component", {"is_earning": 1}, "name") or "Reimbursement",
            "amount": doc.total_claimed_amount or doc.total_claim_amount or getattr(doc, 'total', 0),
            "payroll_date": doc.posting_date,
            "remarks": _(f"Reimbursement for Expense Claim {doc.name}"),
            "reference_document": doc.name,
        })
        add.insert(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(f"Failed creating Additional Salary for Expense Claim {doc.name}: {e}")
