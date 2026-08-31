#!/usr/bin/env python3
import sys
import shutil
import datetime

def stripped(s):
    return s.strip()

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 fix_remaining.py /path/to/hr_console.js")
        sys.exit(1)

    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    done = []
    skipped = []

    # ---- 1. Remove subtitle div (3 lines around "Attendance & Employee Management") ----
    target = "Attendance & Employee Management"
    idx = None
    for i, l in enumerate(lines):
        if stripped(l) == target:
            idx = i
            break
    if idx is not None and stripped(lines[idx-1]).startswith('<div style="color:#888;">') and stripped(lines[idx+1]) == '</div>':
        del lines[idx-1:idx+2]
        done.append("subtitle")
    else:
        skipped.append(("subtitle", "pattern not found around expected line"))

    # ---- 2. Replace Attendance Date input block with From/To Date ----
    idx = None
    for i, l in enumerate(lines):
        if 'id="hr-attendance-date"' in l:
            idx = i
            break
    if idx is not None:
        # scan backward for the wrapping div with min-width
        start = None
        for j in range(idx, max(idx-15, -1), -1):
            if "min-width:220px" in lines[j]:
                start = j
                break
        # scan forward for the closing </div>
        end = None
        for j in range(idx, min(idx+10, len(lines))):
            if stripped(lines[j]) == "</div>":
                end = j
                break
        if start is not None and end is not None:
            indent = lines[start][:len(lines[start]) - len(lines[start].lstrip("\t"))]
            new_block = (
                indent + '<div style="display:flex;gap:10px;flex-wrap:wrap;">\n'
                + indent + '\t<div style="min-width:160px;">\n'
                + indent + '\t\t<label style="\n'
                + indent + '\t\t\tdisplay:block;\n'
                + indent + '\t\t\tfont-size:13px;\n'
                + indent + '\t\t\tfont-weight:600;\n'
                + indent + '\t\t\tmargin-bottom:5px;\n'
                + indent + '\t\t">\n'
                + indent + '\t\t\tFrom Date\n'
                + indent + '\t\t</label>\n'
                + indent + '\t\t<input\n'
                + indent + '\t\t\ttype="date"\n'
                + indent + '\t\t\tid="hr-from-date"\n'
                + indent + '\t\t\tclass="form-control"\n'
                + indent + '\t\t\tvalue="${selectedDate}"\n'
                + indent + '\t\t/>\n'
                + indent + '\t</div>\n'
                + indent + '\t<div style="min-width:160px;">\n'
                + indent + '\t\t<label style="\n'
                + indent + '\t\t\tdisplay:block;\n'
                + indent + '\t\t\tfont-size:13px;\n'
                + indent + '\t\t\tfont-weight:600;\n'
                + indent + '\t\t\tmargin-bottom:5px;\n'
                + indent + '\t\t">\n'
                + indent + '\t\t\tTo Date\n'
                + indent + '\t\t</label>\n'
                + indent + '\t\t<input\n'
                + indent + '\t\t\ttype="date"\n'
                + indent + '\t\t\tid="hr-to-date"\n'
                + indent + '\t\t\tclass="form-control"\n'
                + indent + '\t\t\tvalue="${selectedDate}"\n'
                + indent + '\t\t/>\n'
                + indent + '\t</div>\n'
                + indent + '</div>\n'
            )
            del lines[start:end+1]
            lines.insert(start, new_block)
            done.append("date_filter")
        else:
            skipped.append(("date_filter", "could not locate block boundaries"))
    else:
        skipped.append(("date_filter", "hr-attendance-date id not found"))

    # ---- 3. Remove yellow button (Open Attendance Review Queue) ----
    idx = None
    for i, l in enumerate(lines):
        if stripped(l) == 'id="hr-review"':
            idx = i
            break
    if idx is not None:
        start = None
        for j in range(idx, max(idx-5, -1), -1):
            if stripped(lines[j]) == "<button":
                start = j
                break
        end = None
        for j in range(idx, min(idx+6, len(lines))):
            if stripped(lines[j]) == "</button>":
                end = j
                break
        if start is not None and end is not None:
            del lines[start:end+1]
            done.append("yellow_button")
        else:
            skipped.append(("yellow_button", "could not locate button boundaries"))
    else:
        skipped.append(("yellow_button", 'id="hr-review" not found (already removed?)'))

    # ---- 4. Fix loadEmployees args: attendance_date: selectedDate -> from_date/to_date ----
    idx = None
    for i, l in enumerate(lines):
        if stripped(l) == "attendance_da~e:":
            idx = i
            break
    if idx is not None and stripped(lines[idx+1]).rstrip(",") == "selectedDate":
        indent = lines[idx][:len(lines[idx]) - len(lines[idx].lstrip("\t"))]
        new_block = (
            indent + "from_date:\n"
            + indent + "\tfromDate,\n"
            + indent + "to_date:\n"
            + indent + "\ttoDate,\n"
        )
        del lines[idx:idx+2]
        lines.insert(idx, new_block)
        done.append("employees_args")
    else:
        skipped.append(("employees_args", "attendance_date: selectedDate pattern not found"))

    if not done:
        print("Nothing changed.")
        sys.exit(1)

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = "%s.backup_before_fixremaining_%s" % (path, stamp)
    shutil.copy2(path, backup_path)
    print("Backup saved: %s" % backup_path)

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print("\nApplied: %s" % ", ".join(done))
    if skipped:
        print("\nSTILL NOT APPLIED:")
        for name, reason in skipped:
            print("  - %s: %s" % (name, reason))

if __name__ == "__main__":
    main()
