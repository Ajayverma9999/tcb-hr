import frappe
from frappe import _


def _ensure_system_or_hr():
    if not (("HR Manager" in frappe.get_roles()) or ("System Manager" in frappe.get_roles())):
        frappe.throw(_("Not permitted"), frappe.PermissionError)


@frappe.whitelist()
def get_settings():
    _ensure_system_or_hr()
    doc = frappe.get_single('HR Settings')
    return {
        'standard_hours_per_day': doc.get('standard_hours_per_day'),
        'saturday_policy': doc.get('saturday_policy'),
        'payroll_lock_day': doc.get('payroll_lock_day'),
        'payroll_auto_create_draft': bool(doc.get('payroll_auto_create_draft')),
        'leave_default_advance_days': doc.get('leave_default_advance_days'),
    }


@frappe.whitelist()
def set_settings(**kwargs):
    _ensure_system_or_hr()
    doc = frappe.get_single('HR Settings')
    for k, v in kwargs.items():
        if k in ('standard_hours_per_day', 'saturday_policy', 'payroll_lock_day', 'payroll_auto_create_draft', 'leave_default_advance_days'):
            # coerce checkbox
            if k == 'payroll_auto_create_draft':
                doc.set(k, True if v in (True, '1', 'true', 'True') else False)
            else:
                doc.set(k, v)
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {'status': 'ok'}


def apply_saturday_policy(year=None, month=None):
	"""Sync Saturdays for the given month (default: next month) into each
	company's default Holiday List according to HR Settings.saturday_policy.

	- Full: no change, Saturdays are normal working days.
	- Half: Saturdays remain working (paid) days; nothing added to Holiday
	  List, but marked so Attendance/Payroll logic can treat them as
	  half-day-target if needed (handled by the calendar, not by removing
	  the day from Holiday List).
	- Off: every Saturday in the month is added to each company's default
	  Holiday List as a holiday (if not already present).
	"""
	import calendar
	from frappe.utils import getdate, add_months, nowdate

	hr = frappe.get_single("HR Settings")
	policy = hr.get("saturday_policy")

	if not policy or policy == "Full":
		return {"status": "skipped", "reason": "Policy is Full or not set"}

	if not year or not month:
		target = add_months(nowdate(), 1)
		target = getdate(target)
		year, month = target.year, target.month

	# Find all Saturdays in the target month
	_, days_in_month = calendar.monthrange(year, month)
	saturdays = []
	for day in range(1, days_in_month + 1):
		d = getdate(f"{year}-{month:02d}-{day:02d}")
		if d.weekday() == 5:  # Monday=0 ... Saturday=5
			saturdays.append(d)

	if policy != "Off":
		# Half policy: nothing to add to Holiday List; Saturdays stay working
		# (paid) days. Just report which Saturdays were identified.
		return {"status": "ok", "policy": policy, "saturdays": [str(s) for s in saturdays], "added": []}

	# Off policy: add each Saturday as a holiday in every company's default Holiday List
	companies = frappe.get_all("Company", fields=["name", "default_holiday_list"])
	added = []

	for c in companies:
		if not c.default_holiday_list:
			continue

		hl = frappe.get_doc("Holiday List", c.default_holiday_list)
		existing_dates = {getdate(h.holiday_date) for h in hl.holidays}

		changed = False
		for sat in saturdays:
			if sat in existing_dates:
				continue
			hl.append("holidays", {
				"holiday_date": sat,
				"description": "Saturday Off (auto, Saturday Policy)",
				"weekly_off": 1,
			})
			added.append({"company": c.name, "holiday_list": hl.name, "date": str(sat)})
			changed = True

		if changed:
			hl.save(ignore_permissions=True)

	frappe.db.commit()
	return {"status": "ok", "policy": policy, "saturdays": [str(s) for s in saturdays], "added": added}
