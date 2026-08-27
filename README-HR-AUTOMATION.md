HR Automation — Developer Quick Run

This document lists quick commands to finish setup and run basic checks for the HR Automation customizations in this app.

Prerequisites
- You must run these commands from the bench instance that hosts the site (e.g., `frappe-bench`).
- Run them as a user who can invoke `bench` commands and has access to the site database.

1) Create roles and assign Attendance Approver to HR users

Run as System Manager / Administrator from your bench root:

```bash
# create roles and assign
bench --site tcb.local execute tcb_customization.tcb_customization.api.roles.run_ensure_roles

# apply Attendance permissions to the Attendance DocType
bench --site tcb.local execute tcb_customization.tcb_customization.api.permissions.apply_attendance_permissions
```

2) Ensure custom fields are present

```bash
bench --site tcb.local execute "from tcb_customization.tcb_customization.api.custom_fields import ensure_hr_custom_fields; ensure_hr_custom_fields()"
```

3) Run quick sanity checks (no DB changes): get overview

Open the Desk and visit the Page `HR Console` (create a Page named "HR Console" if necessary) or call the API:

```bash
bench --site tcb.local execute "import frappe; print(frappe.get_attr('tcb_customization.tcb_customization.api.hr_console.get_overview')())"
```

Notes on testing
- Full end-to-end tests require a running Frappe/ERPNext site with demo or seeded data, and are not executed by these scripts.
- For integration tests, run in a staging copy of your site and verify attendance, leave split, and payroll draft flows by creating sample employees and running the scheduled jobs (or invoking them via `bench execute`).
