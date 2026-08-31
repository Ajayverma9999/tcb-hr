#!/usr/bin/env python3
import sys
import shutil
import datetime

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 apply_hr_console_changes.py /path/to/hr_console.js")
        sys.exit(1)

    path = sys.argv[1]

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    original = content
    replacements = []

    old = '''					<div>
						<h2 style="margin:0 0 5px 0;">
							HR Console
						</h2>
						<div style="color:#888;">
							Attendance & Employee Management
						</div>
					</div>'''
    new = '''					<div>
						<h2 style="margin:0 0 5px 0;">
							HR Console
						</h2>
					</div>'''
    replacements.append(("subtitle", old, new))

    old = '''					<div style="min-width:220px;">
						<label style="
							display:block;
							font-size:13px;
							font-weight:600;
							margin-bottom:5px;
						">
							Attendance Date
						</label>
						<input
							type="date"
							id="hr-attendance-date"
							class="form-control"
							value="${selectedDate}"
						/>
					</div>'''
    new = '''					<div style="display:flex;gap:10px;flex-wrap:wrap;">
						<div style="min-width:160px;">
							<label style="
								display:block;
								font-size:13px;
								font-weight:600;
								margin-bottom:5px;
							">
								From Date
							</label>
							<input
								type="date"
								id="hr-from-date"
								class="form-control"
								value="${selectedDate}"
							/>
						</div>
						<div style="min-width:160px;">
							<label style="
								display:block;
								font-size:13px;
								font-weight:600;
								margin-bottom:5px;
							">
								To Date
							</label>
							<input
								type="date"
								id="hr-to-date"
								class="form-control"
								value="${selectedDate}"
							/>
						</div>
					</div>'''
    replacements.append(("date_filter", old, new))

    old = '''				<div
					id="hr-selected-status"
					style="
						margin-bottom:15px;
						font-weight:600;
						color:#555;
					"
				>
					Active Employees — ${selectedDate}
				</div>
'''
    new = ""
    replacements.append(("status_line", old, new))

    old = '''					<button
						class="btn btn-primary"
						id="hr-refresh"
					>
						Refresh
					</button>
					<button
						class="btn btn-warning"
						id="hr-review"
					>
						Open Attendance Review Queue
					</button>'''
    new = '''					<button
						class="btn btn-primary"
						id="hr-refresh"
					>
						Refresh
					</button>'''
    replacements.append(("yellow_button", old, new))

    old = '\t\tconst $date = $main.find("#hr-attendance-date");'
    new = '\t\tconst $fromDate = $main.find("#hr-from-date");\n\t\tconst $toDate = $main.find("#hr-to-date");'
    replacements.append(("var_decl", old, new))

    old = "\t\tlet selectedDate = frappe.datetime.get_today();"
    new = ("\t\tlet selectedDate = frappe.datetime.get_today();\n"
           "\t\tlet fromDate = frappe.datetime.get_today();\n"
           "\t\tlet toDate = frappe.datetime.get_today();")
    replacements.append(("state_vars", old, new))

    old = '''				args: {
					from_date: selectedDate,
					to_date: selectedDate,
					attendance_date: selectedDate,
				},'''
    new = '''				args: {
					from_date: fromDate,
					to_date: toDate,
				},'''
    replacements.append(("overview_args", old, new))

    old = '''				args: {
					attendance_date:
						selectedDate,
					status:
						currentStatus,'''
    new = '''				args: {
					from_date:
						fromDate,
					to_date:
						toDate,
					status:
						currentStatus,'''
    replacements.append(("employees_args", old, new))

    old = '''		$date.on(
			"change",
			function () {

				selectedDate =
					$(this).val() ||
					frappe.datetime.get_today();

				currentPage = 0;
				selectedEmployee = null;

				updateStatusLabel();

				$detail.html(`
					<h4>
						Employee Details
					</h4>

					<p style="color:#888;">
						Select an employee from the list.
					</p>
				`);

				loadOverview();

				loadEmployees(0);
			}
		);'''
    new = '''		function handleDateRangeChange() {

			fromDate =
				$fromDate.val() ||
				frappe.datetime.get_today();

			toDate =
				$toDate.val() ||
				frappe.datetime.get_today();

			selectedDate = toDate;

			currentPage = 0;
			selectedEmployee = null;

			$detail.html(`
				<h4>
					Employee Details
				</h4>

				<p style="color:#888;">
					Select an employee from the list.
				</p>
			`);

			loadOverview();

			loadEmployees(0);
		}

		$fromDate.on("change", handleDateRangeChange);
		$toDate.on("change", handleDateRangeChange);'''
    replacements.append(("date_handler", old, new))

    failed = []
    applied = []
    for name, old, new in replacements:
        count = content.count(old)
        if count == 1:
            content = content.replace(old, new)
            applied.append(name)
        elif count == 0:
            failed.append((name, "not found (maybe already applied or file differs)"))
        else:
            failed.append((name, "found %d times, expected exactly 1 - skipped for safety" % count))

    if content == original:
        print("No changes were applied. Nothing matched.")
        sys.exit(1)

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = "%s.backup_before_daterange_%s" % (path, stamp)
    shutil.copy2(path, backup_path)
    print("Backup saved: %s" % backup_path)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    print("\nApplied %d/9 changes: %s" % (len(applied), ", ".join(applied)))
    if failed:
        print("\nCOULD NOT APPLY (please check manually):")
        for name, reason in failed:
            print("  - %s: %s" % (name, reason))
    else:
        print("\nAll 9 changes applied successfully.")

if __name__ == "__main__":
    main()
