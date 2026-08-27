import frappe


def ensure_hr_custom_fields():
    """Create custom fields used by HR workflows if they don't exist."""
    to_create = [
        # (doctype, fieldname, fieldtype, label, options, insert_after)
        ("Leave Type", "advance_notice_days", "Int", "Advance Notice Days", None, "max_leave_days"),
        ("Leave Application", "hr_override", "Check", "HR Override", None, "reason"),
        ("Leave Application", "manager_approved", "Check", "Manager Approved", None, "hr_override"),
        ("Leave Application", "hr_approved", "Check", "HR Approved", None, "manager_approved"),
        ("Attendance", "timesheet", "Link", "Timesheet", "Timesheet", "attendance_date"),
        ("Attendance", "hr_note", "Small Text", "HR Note", None, "status"),
    ]

    # HR Settings single
    to_create += [
        ("HR Settings", "standard_hours_per_day", "Float", "Standard Hours Per Day", None, "working_hours"),
        ("HR Settings", "saturday_policy", "Select", "Saturday Policy", "Full\nHalf\nOff", "standard_hours_per_day"),
        ("HR Settings", "payroll_lock_day", "Int", "Payroll Lock Day (day of month)", None, "saturday_policy"),
        ("HR Settings", "payroll_auto_create_draft", "Check", "Auto-create Payroll Drafts", None, "payroll_lock_day"),
        ("HR Settings", "leave_default_advance_days", "Int", "Default Leave Advance Notice Days", None, "payroll_auto_create_draft"),
        ("HR Settings", "timesheet_reminder_enabled", "Check", "Enable Timesheet Reminders", None, "leave_default_advance_days"),
        ("HR Settings", "timesheet_auto_apply_lwp", "Check", "Auto-apply LWP on no timesheet", None, "timesheet_reminder_enabled"),
    ]

    for dt, fieldname, ftype, label, options, insert_after in to_create:
        exists = frappe.get_all(
            "Custom Field", filters={"dt": dt, "fieldname": fieldname}, limit_page_length=1
        )
        if exists:
            continue

        doc = frappe.get_doc(
            {
                "doctype": "Custom Field",
                "dt": dt,
                "fieldname": fieldname,
                "label": label,
                "fieldtype": ftype,
                "insert_after": insert_after,
            }
        )
        if options:
            doc.options = options
        try:
            doc.insert(ignore_permissions=True)
            frappe.db.commit()
        except Exception as e:
            frappe.log_error(f"Failed to create custom field {fieldname} on {dt}: {e}")


def ensure_leave_workflow():
    """Create a Workflow for Leave Application: Manager -> HR approval."""
    if frappe.db.exists("Workflow", "Leave Application: Manager HR"):
        return

    # Ensure HR Manager role exists
    if not frappe.db.exists("Role", "HR Manager"):
        frappe.get_doc(doctype="Role", role_name="HR Manager").insert(ignore_if_duplicate=True)

    workflow = frappe.new_doc("Workflow")
    workflow.workflow_name = "Leave Application: Manager HR"
    workflow.document_type = "Leave Application"
    workflow.workflow_state_field = "status"
    workflow.is_active = 1
    workflow.send_email_alert = 1

    # States
    workflow.append("states", dict(state="Draft", allow_edit="Employee"))
    workflow.append("states", dict(state="Pending Manager Approval", allow_edit="All"))
    workflow.append("states", dict(state="Pending HR Approval", allow_edit="HR Manager"))
    workflow.append("states", dict(state="Approved", allow_edit="HR Manager"))
    workflow.append("states", dict(state="Rejected", allow_edit="HR Manager"))

    # Transitions
    # Employee submits -> Pending Manager Approval
    workflow.append(
        "transitions",
        dict(state="Draft", action="Submit for Approval", next_state="Pending Manager Approval", allowed="Employee", allow_self_approval=1),
    )

    # Manager approves -> Pending HR Approval (limit to reporting manager via condition)
    workflow.append(
        "transitions",
        dict(
            state="Pending Manager Approval",
            action="Manager Approve",
            next_state="Pending HR Approval",
            allowed="All",
            allow_self_approval=0,
            condition='frappe.db.get_value("Employee", doc.employee, "user_id") == frappe.session.user',
        ),
    )

    # HR approves -> Approved
    workflow.append(
        "transitions",
        dict(state="Pending HR Approval", action="HR Approve", next_state="Approved", allowed="HR Manager", allow_self_approval=0),
    )

    # Reject action from manager or HR
    workflow.append(
        "transitions",
        dict(state="Pending Manager Approval", action="Reject", next_state="Rejected", allowed="All", allow_self_approval=0),
    )
    workflow.append(
        "transitions",
        dict(state="Pending HR Approval", action="Reject", next_state="Rejected", allowed="HR Manager", allow_self_approval=0),
    )

    try:
        workflow.insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Failed to create Leave Application workflow: {e}")


def ensure_hr_customization():
    ensure_hr_custom_fields()
    ensure_leave_workflow()
