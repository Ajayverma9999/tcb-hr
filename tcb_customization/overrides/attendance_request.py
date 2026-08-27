import frappe
from hrms.hr.doctype.attendance_request.attendance_request import AttendanceRequest as BaseAttendanceRequest
from frappe import _


class CustomAttendanceRequest(BaseAttendanceRequest):
    def on_submit(self):
        # If this is a Work From Home request, route for approvals instead of creating attendance immediately
        if getattr(self, "reason", "") == "Work From Home":
            # Ensure custom fields exist
            from tcb_customization.api.wfh_workflow import ensure_custom_fields

            ensure_custom_fields()

            # set status to Pending Manager Approval

            # set reporting manager on the request if available
            reports_to = frappe.get_value("Employee", self.employee, "reports_to")
            if reports_to:
                self.db_set("manager", reports_to)

            # Notify reporting manager (if user linked)
            user = frappe.get_value("Employee", reports_to, "user_id")
            if user:
                frappe.get_doc({
                    "doctype": "Notification Log",
                    "subject": "Attendance Request: Manager approval required",
                    "for_user": user,
                    "email_content": _(
                        "Please review Attendance Request {0} for {1}."
                    ).format(self.name, self.employee),
                    "type": "Alert",
                }).insert(ignore_permissions=True)

            return

        # Fallback to default behaviour for non-WFH reasons
        super().on_submit()
