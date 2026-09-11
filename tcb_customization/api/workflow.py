import frappe
from frappe.model.workflow import apply_workflow as original_apply_workflow


@frappe.whitelist()
def apply_workflow(doc, action):
    doc = frappe.get_doc(frappe.parse_json(doc))
    doc.load_from_db()

    if doc.doctype == "Leave Application":
        workflow_state = doc.get("workflow_state")

        if workflow_state == "Pending Reporting Approval":
            reporting_manager = frappe.db.get_value(
                "Employee",
                doc.employee,
                "reports_to",
            )

            if not reporting_manager:
                frappe.throw(
                    "This employee does not have a Reporting Manager assigned."
                )

            manager_user = frappe.db.get_value(
                "Employee",
                reporting_manager,
                "user_id",
            )

            if not manager_user:
                frappe.throw(
                    "The Reporting Manager does not have a User ID assigned."
                )

            if frappe.session.user != manager_user:
                frappe.throw(
                    "Only the employee's Reporting Manager can approve or reject this leave application."
                )

    return original_apply_workflow(
        frappe.as_json(doc),
        action,
    )
