#!/usr/bin/env bash
# Helper to run initial setup actions for tcb_customization on a site
SITE=${1:-tcb.local}
echo "Running role & permission setup on site: $SITE"
bench --site "$SITE" execute "tcb_customization.api.roles.run_ensure_roles"
bench --site "$SITE" execute "tcb_customization.api.permissions.apply_attendance_permissions_cli"
bench --site "$SITE" execute "tcb_customization.api.custom_fields.ensure_hr_custom_fields"
echo "Done. Review output above for created roles/permissions and any errors."
