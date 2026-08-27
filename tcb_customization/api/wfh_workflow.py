import frappe
from frappe import _
from frappe.utils import getdate, nowdate


def ensure_custom_fields():
    """Create small set of Custom Fields on Attendance Request if missing.

    Fields: manager (Link: Employee), manager_approved (Check), hr_approved (Check)
    """
    cf_list = [
        ("manager", "Link", "Employee", "Reporting Manager", "status"),
        ("manager_approved", "Check", None, "Manager Approved", "manager"),
        ("hr_approved", "Check", None, "HR Approved", "manager_approved"),
    ]

    for fieldname, fieldtype, options, label, insert_after in cf_list:
        exists = frappe.get_all(
            "Custom Field", filters={"dt": "Attendance Request", "fieldname": fieldname}, limit_page_length=1
        )
        if not exists:
            doc = frappe.get_doc(
                {
                    "doctype": "Custom Field",
                    "dt": "Attendance Request",
                    "fieldname": fieldname,
                    "label": label,
                    "fieldtype": fieldtype,
                    "insert_after": insert_after,
                }
            )
            if options:
                doc.options = options
            try:
                doc.insert(ignore_permissions=True)
                frappe.db.commit()
            except Exception:
                frappe.log_error(f"Failed to create custom field {fieldname} on Attendance Request")


@frappe.whitelist()
def manager_approve(name):
    """Called by reporting manager to approve the Attendance Request for WFH."""
    user = frappe.session.user
    req = frappe.get_doc("Attendance Request", name)
    if req.reason != "Work From Home":
        frappe.throw("This approval flow is for Work From Home requests only.")

    # ensure fields
    ensure_custom_fields()

    reports_to = frappe.get_value("Employee", req.employee, "reports_to")
    if not reports_to:
        frappe.throw("Employee has no reporting manager configured.")

    manager_user = frappe.get_value("Employee", reports_to, "user_id")
    if manager_user != user:
        frappe.throw("Only the reporting manager can approve this request.")

    req.db_set("manager_approved", 1)

    # notify HR Managers
    hr_users = frappe.get_all("Has Role", filters={"role": "HR Manager"}, fields=["parent as user"])
    for r in hr_users:
        try:
            frappe.get_doc(
                {
                    "doctype": "Notification Log",
                    "subject": "Attendance Request: HR approval required",
                    "for_user": r.user,
                    "email_content": _(
                        "Please review Attendance Request {0} for {1}."
                    ).format(req.name, req.employee),
                    "type": "Alert",
                }
            ).insert(ignore_permissions=True)
        except Exception:
            pass

    return {"status": "manager_approved"}


@frappe.whitelist()
def hr_approve(name):
    """Called by HR Manager to finally approve and mark Attendance as Work From Home."""
    if not (("HR Manager" in frappe.get_roles()) or ("System Manager" in frappe.get_roles())):
        frappe.throw("Only HR Manager or System Manager can approve this request.")

    req = frappe.get_doc("Attendance Request", name)
    if req.reason != "Work From Home":
        frappe.throw("This approval flow is for Work From Home requests only.")

    ensure_custom_fields()

    if not req.get("manager_approved"):
        frappe.throw("Request must be approved by reporting manager first.")

    # mark HR approved
    req.db_set("hr_approved", 1)

    # Create attendance records as Work From Home
    try:
        req.create_attendance_records()
    except Exception as e:
        frappe.log_error(f"Failed creating attendance records for Attendance Request {name}: {e}")
        frappe.throw("Failed to create attendance records; check error logs.")

    # add an audit comment
    req.add_comment("Comment", f"Approved by HR: {frappe.session.user} on {nowdate()}")

    # notify employee
    user = frappe.get_value("Employee", req.employee, "user_id")
    if user:
        frappe.get_doc(
            {
                "doctype": "Notification Log",
                "subject": "Your Work From Home request was approved",
                "for_user": user,
                "email_content": _(
                    "Your Work From Home Attendance Request {0} has been approved by HR."
                ).format(req.name),
                "type": "Alert",
            }
        ).insert(ignore_permissions=True)

    return {"status": "hr_approved"}


@frappe.whitelist()
def manager_approve_leave(name):
    """Called by reporting manager to mark Leave Application as manager_approved."""
    user = frappe.session.user
    req = frappe.get_doc("Leave Application", name)

    reports_to = frappe.get_value("Employee", req.employee, "reports_to")
    if not reports_to:
        frappe.throw("Employee has no reporting manager configured.")

    manager_user = frappe.get_value("Employee", reports_to, "user_id")
    if manager_user != user:
        frappe.throw("Only the reporting manager can approve this leave request.")

    req.db_set("manager_approved", 1)

    # notify HR Managers
    hr_users = frappe.get_all("Has Role", filters={"role": "HR Manager"}, fields=["parent as user"]) 
    for r in hr_users:
        try:
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": "Leave Application: HR approval required",
                "for_user": r.user,
                "email_content": _("Please review Leave Application {0} for {1}.").format(req.name, req.employee),
                "type": "Alert",
            }).insert(ignore_permissions=True)
        except Exception:
            pass

    return {"status": "manager_approved"}


@frappe.whitelist()
def hr_approve_leave(name):
    """Called by HR Manager to finalize Leave Application approval."""
    if not (("HR Manager" in frappe.get_roles()) or ("System Manager" in frappe.get_roles())):
        frappe.throw("Only HR Manager or System Manager can approve this request.")

    req = frappe.get_doc("Leave Application", name)

    if not req.get("manager_approved"):
        frappe.throw("Request must be approved by reporting manager first.")

    req.db_set("hr_approved", 1)

    # add an audit comment
    req.add_comment("Comment", f"Approved by HR: {frappe.session.user} on {nowdate()}")

    # notify employee
    user = frappe.get_value("Employee", req.employee, "user_id")
    if user:
        try:
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": "Your Leave Application was approved",
                "for_user": user,
                "email_content": _("Your Leave Application {0} has been approved by HR.").format(req.name),
                "type": "Alert",
            }).insert(ignore_permissions=True)
        except Exception:
            pass

    return {"status": "hr_approved"}


def notify_manager_attendance_request(doc, method=None):
	"""on_submit hook for Attendance Request (WFH) - notify reporting manager."""
	if doc.reason != "Work From Home":
		return

	ensure_custom_fields()

	reports_to = frappe.get_value("Employee", doc.employee, "reports_to")
	if not reports_to:
		frappe.log_error(f"No reporting manager for employee {doc.employee}", "WFH Notify Manager")
		return

	manager_user = frappe.get_value("Employee", reports_to, "user_id")


	if manager_user:
		try:
			frappe.get_doc(
				{
					"doctype": "Notification Log",
					"subject": "New WFH request needs your approval",
					"for_user": manager_user,
					"email_content": _(
						"{0} has submitted a Work From Home request ({1}) that needs your approval."
					).format(doc.employee_name or doc.employee, doc.name),
					"type": "Alert",
				}
			).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "WFH Notify Manager - Notification Failed")


def notify_manager_leave_application(doc, method=None):
	"""on_submit hook for Leave Application - notify reporting manager."""
	reports_to = frappe.get_value("Employee", doc.employee, "reports_to")
	if not reports_to:
		frappe.log_error(f"No reporting manager for employee {doc.employee}", "Leave Notify Manager")
		return

	manager_user = frappe.get_value("Employee", reports_to, "user_id")


	if manager_user:
		try:
			frappe.get_doc(
				{
					"doctype": "Notification Log",
					"subject": "New Leave Application needs your approval",
					"for_user": manager_user,
					"email_content": _(
						"{0} has submitted a Leave Application ({1}) that needs your approval."
					).format(doc.employee_name or doc.employee, doc.name),
					"type": "Alert",
				}
			).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Leave Notify Manager - Notification Failed")
