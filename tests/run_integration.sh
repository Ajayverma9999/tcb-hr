#!/usr/bin/env bash
# Simple integration smoke test for tcb_customization
SITE=${1:-tcb.local}
echo "Running integration smoke tests on site: $SITE"

echo "1) Ensure roles & permissions"
bench --site "$SITE" execute "tcb_customization.api.roles.ensure_roles"
bench --site "$SITE" execute "tcb_customization.api.permissions.apply_attendance_permissions_cli"

echo "2) Ensure custom fields"
bench --site "$SITE" execute "tcb_customization.api.custom_fields.ensure_hr_custom_fields"

echo "3) Run attendance pending review check (yesterday)"
bench --site "$SITE" execute "tcb_customization.api.attendance_job.get_pending_reviews"

echo "4) Run payroll draft job (dry-run)"
bench --site "$SITE" execute "tcb_customization.api.payroll_job.create_monthly_payroll_draft"

echo "Smoke tests finished. Review outputs above for errors."
