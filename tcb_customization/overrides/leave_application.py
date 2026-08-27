import frappe
from hrms.hr.doctype.leave_application.leave_application import LeaveApplication as BaseLeaveApplication
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on, get_number_of_leave_days
from frappe import _
from datetime import timedelta


class CustomLeaveApplication(BaseLeaveApplication):
    def on_submit(self):
        # Route for manager -> HR approval when employee has a reporting manager
        try:
            from tcb_customization.api.wfh_workflow import ensure_custom_fields
        except Exception:
            ensure_custom_fields = None

        if hasattr(self, 'employee') and self.employee:
            reports_to = frappe.get_value("Employee", self.employee, "reports_to")
            if reports_to:
                # ensure custom fields exist
                if ensure_custom_fields:
                    try:
                        ensure_custom_fields()
                    except Exception:
                        pass

                # set status (reports_to fetched live from Employee, no separate manager field needed)
                self.db_set('status', 'Pending Manager Approval')

                # notify reporting manager
                user = frappe.get_value('Employee', reports_to, 'user_id')
                if user:
                    try:
                        frappe.get_doc({
                            'doctype': 'Notification Log',
                            'subject': 'Leave Application: Manager approval required',
                            'for_user': user,
                            'email_content': _("Please review Leave Application {0} for {1}.").format(self.name, self.employee),
                            'type': 'Alert'
                        }).insert(ignore_permissions=True)
                    except Exception:
                        pass
                return

        # fallback to default behaviour
        return super().on_submit()
    def validate_balance_leaves(self):
        # Attempt normal validation, but auto-split if insufficient balance
        try:
            super().validate_balance_leaves()
        except Exception as e:
            # If it's not an insufficient balance error, re-raise
            if "Insufficient leave balance" not in str(e):
                raise

            # compute remaining leave balance for consumption
            leave_balance = get_leave_balance_on(
                self.employee,
                self.leave_type,
                self.from_date,
                to_date=self.to_date,
                consider_all_leaves_in_the_allocation_period=True,
                for_consumption=True,
            )
            available = float(leave_balance.get("leave_balance_for_consumption") or 0)

            # If nothing available, convert entire application to Leave Without Pay
            if available <= 0:
                lwp_type = frappe.get_value("Leave Type", {"is_lwp": 1}, "name") or "Leave Without Pay"
                frappe.msgprint(
                    _("No paid balance available. Converting application to {0}.").format(lwp_type)
                )
                self.leave_type = lwp_type
                return

            # Determine paid_end_date by consuming full days greedily
            acc = 0.0
            paid_end = None
            cur = frappe.utils.getdate(self.from_date)
            end = frappe.utils.getdate(self.to_date)

            while cur <= end and acc < available:
                day_val = get_number_of_leave_days(self.employee, self.leave_type, cur, cur, self.half_day and frappe.utils.getdate(self.half_day_date) == cur, self.half_day_date)
                if day_val <= 0:
                    cur += timedelta(days=1)
                    continue
                if acc + day_val <= available + 1e-9:
                    acc += day_val
                    paid_end = cur
                    cur += timedelta(days=1)
                else:
                    # partial day (not handling fractions beyond 0.5 precisely)
                    break

            if not paid_end:
                # fallback: no paid days
                lwp_type = frappe.get_value("Leave Type", {"is_lwp": 1}, "name") or "Leave Without Pay"
                self.leave_type = lwp_type
                return

            # If paid_end covers whole application, nothing to split
            if paid_end >= end:
                return

            # Otherwise, shrink current doc to paid part and create LWP doc for remainder
            original_to = self.to_date
            lwp_start = (paid_end + timedelta(days=1)).isoformat()

            # Adjust current document to paid range
            self.to_date = paid_end
            # Recompute total_leave_days for modified doc
            self.total_leave_days = get_number_of_leave_days(
                self.employee,
                self.leave_type,
                self.from_date,
                self.to_date,
                self.half_day,
                self.half_day_date,
            )

            # Create LWP application for remainder
            lwp_type = frappe.get_value("Leave Type", {"is_lwp": 1}, "name") or "Leave Without Pay"
            lwp = frappe.new_doc("Leave Application")
            lwp.update({
                "employee": self.employee,
                "from_date": lwp_start,
                "to_date": original_to,
                "leave_type": lwp_type,
                "company": self.company,
                "reason": self.reason + " (Auto-converted to LWP)",
                "status": self.status,
            })
            try:
                lwp.insert(ignore_permissions=True)
                # auto-submit the LWP so payroll picks it up; keep same workflow as original
                lwp.submit()
            except Exception as e2:
                frappe.log_error(f"Failed to create LWP split for {self.name}: {e2}")
                # If LWP creation fails, raise original error
                raise

            frappe.msgprint(
                _(
                    "Leave application was split: paid part {0} to {1}; unpaid part {2} to {3} created as {4}."
                ).format(self.from_date, self.to_date, lwp.from_date, lwp.to_date, lwp.leave_type)
            )
