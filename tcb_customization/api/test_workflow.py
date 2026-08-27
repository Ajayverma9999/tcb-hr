import frappe
from frappe import _
from frappe.utils import nowdate


def run_leave_workflow_test():
    """Create test users/employees, create a Leave Application and run manager->HR approvals."""
    try:
        # pick a company
        companies = frappe.get_all("Company", limit_page_length=1)
        company = companies[0].name if companies else "Default Company"

        # create users
        mgr_email = "manager_test@example.com"
        emp_email = "employee_test@example.com"
        hr_email = "hr_test@example.com"

        if not frappe.db.exists("User", mgr_email):
            u = frappe.get_doc({"doctype": "User", "email": mgr_email, "first_name": "Test Manager", "enabled": 1})
            u.insert(ignore_permissions=True)

        if not frappe.db.exists("User", emp_email):
            u = frappe.get_doc({"doctype": "User", "email": emp_email, "first_name": "Test Employee", "enabled": 1})
            u.insert(ignore_permissions=True)

        if not frappe.db.exists("User", hr_email):
            u = frappe.get_doc({"doctype": "User", "email": hr_email, "first_name": "Test HR", "enabled": 1})
            u.insert(ignore_permissions=True)

        # Ensure HR Manager role
        if not frappe.db.exists("Role", "HR Manager"):
            frappe.get_doc(doctype="Role", role_name="HR Manager").insert(ignore_if_duplicate=True)

        # assign HR Manager role to hr user
        hr_user = frappe.get_doc("User", hr_email)
        hr_user.add_roles("HR Manager")

        # create employees
        if not frappe.db.exists("Employee", {"user_id": mgr_email}):
            mgr_emp = frappe.get_doc({
                "doctype": "Employee",
                "employee_name": "Test Manager",
                "first_name": "Manager",
                "company": company,
                "user_id": mgr_email,
                "gender": "Other",
                "date_of_birth": "1990-01-01",
                "date_of_joining": nowdate(),
            })
            mgr_emp.insert(ignore_permissions=True)
        else:
            mgr_emp = frappe.get_all("Employee", filters={"user_id": mgr_email}, limit_page_length=1)[0]

        if not frappe.db.exists("Employee", {"user_id": emp_email}):
            emp = frappe.get_doc({
                "doctype": "Employee",
                "employee_name": "Test Employee",
                "first_name": "Employee",
                "company": company,
                "reports_to": mgr_emp if isinstance(mgr_emp, str) else mgr_emp.name,
                "user_id": emp_email,
                "gender": "Other",
                "date_of_birth": "1995-01-01",
                "date_of_joining": nowdate(),
            })
            emp.insert(ignore_permissions=True)
        else:
            emp = frappe.get_all("Employee", filters={"user_id": emp_email}, limit_page_length=1)[0]

        # pick or create a Leave Type
        lt = frappe.get_all("Leave Type", limit_page_length=1)
        leave_type = lt[0].name if lt else "Casual Leave"
        if not frappe.db.exists("Leave Type", leave_type):
            frappe.get_doc({"doctype": "Leave Type", "leave_type": leave_type}).insert(ignore_permissions=True)

        # create Leave Application in Pending Manager Approval state
        leave = frappe.get_doc({
            "doctype": "Leave Application",
            "employee": emp if isinstance(emp, str) else emp.name,
            "leave_type": leave_type,
            "from_date": nowdate(),
            "to_date": nowdate(),
            "status": "Pending Manager Approval",
            "manager": mgr_emp if isinstance(mgr_emp, str) else mgr_emp.name,
        })
        leave.insert(ignore_permissions=True)

        results = {"leave_name": leave.name, "initial_status": leave.status}

        # manager approves
        frappe.set_user(mgr_email)
        try:
            mgr_res = frappe.get_attr("tcb_customization.api.wfh_workflow.manager_approve_leave")(leave.name)
        finally:
            # reset to Administrator for subsequent ops
            frappe.set_user("Administrator")

        results["manager_result"] = mgr_res

        # hr approves
        frappe.set_user(hr_email)
        try:
            hr_res = frappe.get_attr("tcb_customization.api.wfh_workflow.hr_approve_leave")(leave.name)
        finally:
            frappe.set_user("Administrator")

        results["hr_result"] = hr_res

        # refresh leave
        leave = frappe.get_doc("Leave Application", leave.name)
        results["final_status"] = leave.status
        results["manager_approved"] = leave.get("manager_approved")
        results["hr_approved"] = leave.get("hr_approved")

        return results

    except Exception as e:
        frappe.log_error(title="Leave workflow test failed", message=str(e))
        return {"error": str(e)}
