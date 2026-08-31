app_name = "tcb_customization"
app_title = "tcb"
app_publisher = "yes"
app_description = "tcb"
app_email = "tcb@gmail.com"
app_license = "mit"


# scheduler_events = {
#     "cron": {
#         "0 22 * * *": [
#             "tcb_customization.api.timesheet_reminder.first_reminder"
#         ],
#         "30 23 * * *": [
#             "tcb_customization.api.timesheet_reminder.final_reminder"
#         ],
#         "55 23 * * *": [
#             "tcb_customization.api.timesheet_reminder.mark_lwp"
#         ]
#     }
# }



scheduler_events = {
    "cron": {
        "30 0 * * *": [
            "tcb_customization.api.attendance_job.process_previous_day"
        ],
        "0 22 * * *": [
            "tcb_customization.api.timesheet_reminder.first_reminder"
        ],
        "30 23 * * *": [
            "tcb_customization.api.timesheet_reminder.final_reminder"
        ],
        "55 23 * * *": [
            "tcb_customization.api.timesheet_reminder.mark_lwp"
        ]
    }
}

# Monthly payroll draft on 1st at 02:00
scheduler_events["cron"]["0 2 1 * *"] = [
    "tcb_customization.api.payroll_job.create_monthly_payroll_draft"
]

# Saturday policy sync: runs on the 25th of each month at 01:00, applying
# the configured Saturday policy to the FOLLOWING month's calendar so the
# Holiday List is ready before that month's payroll/attendance processing.
scheduler_events["cron"]["0 1 25 * *"] = [
    "tcb_customization.api.hr_settings.apply_saturday_policy"
]
doc_events = {
    "Leave Application": {
        "validate": "tcb_customization.api.leave_validation.validate_leave_notice"
    }
}

# Add Attendance validation hook to prevent edits in locked payroll periods
doc_events.update({
    "Attendance": {
        "validate": "tcb_customization.api.payroll_job.prevent_edit_if_locked"
    },
    "Leave Application": {
        "validate": [
            "tcb_customization.api.leave_validation.validate_leave_notice",
            "tcb_customization.api.payroll_job.prevent_edit_if_locked"
        ]
    },
    "Payroll Entry": {
        "on_submit": "tcb_customization.api.payroll_job.on_payroll_submit"
    }
})

# Timesheet validation: auto-fill employee and require descriptions on time logs
doc_events.update({
    "Timesheet": {
        "validate": "tcb_customization.api.timesheet_hooks.validate_timesheet"
    }
})

# Hook Expense Claim submissions to create Additional Salary for reimbursements
doc_events.update({
    "Expense Claim": {
        "on_submit": "tcb_customization.api.expense_to_payroll.create_additional_salary_for_expense"
    }
})

# Client-side Timesheet customisations
doctype_js = {"Timesheet": "public/js/timesheet.js"}
# Simple HR Console page JS (loads when a Page named "hr-console" is created in Desk)
# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "tcb_customization",
# 		"logo": "/assets/tcb_customization/logo.png",
# 		"title": "tcb",
# 		"route": "/tcb_customization",
# 		"has_permission": "tcb_customization.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/tcb_customization/css/tcb_customization.css"
# app_include_js = "/assets/tcb_customization/js/tcb_customization.js"

# include js, css files in header of web template
# web_include_css = "/assets/tcb_customization/css/tcb_customization.css"
# web_include_js = "/assets/tcb_customization/js/tcb_customization.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "tcb_customization/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "tcb_customization/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "tcb_customization.utils.jinja_methods",
# 	"filters": "tcb_customization.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "tcb_customization.install.before_install"
# after_install = "tcb_customization.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "tcb_customization.uninstall.before_uninstall"
# after_uninstall = "tcb_customization.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "tcb_customization.utils.before_app_install"
# after_app_install = "tcb_customization.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "tcb_customization.utils.before_app_uninstall"
# after_app_uninstall = "tcb_customization.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "tcb_customization.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "tcb_customization.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"tcb_customization.tasks.all"
# 	],
# 	"daily": [
# 		"tcb_customization.tasks.daily"
# 	],
# 	"hourly": [
# 		"tcb_customization.tasks.hourly"
# 	],
# 	"weekly": [
# 		"tcb_customization.tasks.weekly"
# 	],
# 	"monthly": [
# 		"tcb_customization.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "tcb_customization.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "tcb_customization.custom.task.CustomTaskMixin"
# }
extend_doctype_class = {
    "Attendance Request": "tcb_customization.overrides.attendance_request.CustomAttendanceRequest",
    "Leave Application": "tcb_customization.overrides.leave_application.CustomLeaveApplication",
}

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "tcb_customization.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "tcb_customization.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["tcb_customization.utils.before_request"]
# after_request = ["tcb_customization.utils.after_request"]

# Job Events
# ----------
# before_job = ["tcb_customization.utils.before_job"]
# after_job = ["tcb_customization.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"tcb_customization.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []


# Notify reporting manager on submission of WFH / Leave requests
doc_events.update({
    "Attendance Request": {
        "on_submit": "tcb_customization.api.wfh_workflow.notify_manager_attendance_request"
    },
    "Leave Application": {
        "validate": [
            "tcb_customization.api.leave_validation.validate_leave_notice",
            "tcb_customization.api.payroll_job.prevent_edit_if_locked",
            "tcb_customization.api.leave_validation.validate_manager_verification"
        ],
        "on_submit": "tcb_customization.api.wfh_workflow.notify_manager_leave_application"
    }
})
