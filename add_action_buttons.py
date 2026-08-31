#!/usr/bin/env python3
import sys
import shutil
import datetime

def stripped(s):
    return s.strip()

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 add_action_buttons.py /path/to/hr_console.js")
        sys.exit(1)

    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    done = []
    skipped = []

    # ---- 1. Add 3 buttons after the Refresh button, inside the actions div ----
    idx = None
    for i, l in enumerate(lines):
        if stripped(l) == 'id="hr-refresh"':
            idx = i
            break
    if idx is not None:
        # find the </button> closing this Refresh button
        end = None
        for j in range(idx, min(idx+6, len(lines))):
            if stripped(lines[j]) == "</button>":
                end = j
                break
        if end is not None:
            indent = lines[idx][:len(lines[idx]) - len(lines[idx].lstrip("\t"))]
            # id line indent, button tag is one level up
            btn_indent = indent[:-1] if len(indent) > 0 else indent
            new_block = (
                btn_indent + '<button\n'
                + indent + 'class="btn btn-default"\n'
                + indent + 'id="hr-wfh-apply"\n'
                + btn_indent + '>\n'
                + indent + 'Apply Work From Home\n'
                + btn_indent + '</button>\n'
                + btn_indent + '<button\n'
                + indent + 'class="btn btn-default"\n'
                + indent + 'id="hr-leave-application"\n'
                + btn_indent + '>\n'
                + indent + 'Apply Leave\n'
                + btn_indent + '</button>\n'
                + btn_indent + '<button\n'
                + indent + 'class="btn btn-default"\n'
                + indent + 'id="hr-expense-claim"\n'
                + btn_indent + '>\n'
                + indent + 'Expense Claim\n'
                + btn_indent + '</button>\n'
            )
            lines.insert(end + 1, new_block)
            done.append("buttons_html")
        else:
            skipped.append(("buttons_html", "could not find closing </button> for Refresh"))
    else:
        skipped.append(("buttons_html", 'id="hr-refresh" not found'))

    # ---- 2. Add click handlers, right after the existing #hr-refresh click handler block ----
    idx = None
    for i, l in enumerate(lines):
        if '.find("#hr-refresh")' in l:
            idx = i
            break
    if idx is not None:
        # find the matching end of this .on("click", function(){...}); block
        # search forward for a line that is just ");" at the same base indent, after seeing "function ()" and its own "}"
        depth = 0
        started = False
        func_closed_at = None
        for j in range(idx, len(lines)):
            depth += lines[j].count("{") - lines[j].count("}")
            if "function" in lines[j]:
                started = True
            if started and depth <= 0 and j > idx:
                func_closed_at = j
                break
        end = None
        if func_closed_at is not None:
            for k in range(func_closed_at, min(func_closed_at + 5, len(lines))):
                if stripped(lines[k]) == ");":
                    end = k
                    break
        if end is not None:
            indent = lines[idx][:len(lines[idx]) - len(lines[idx].lstrip("\t"))]
            new_block = (
                "\n"
                + indent + '$main\n'
                + indent + '\t.find("#hr-wfh-apply")\n'
                + indent + '\t.on(\n'
                + indent + '\t\t"click",\n'
                + indent + '\t\tfunction () {\n'
                + indent + '\t\t\tfrappe.new_doc(\n'
                + indent + '\t\t\t\t"Attendance Request",\n'
                + indent + '\t\t\t\t{ reason: "Work From Home" }\n'
                + indent + '\t\t\t);\n'
                + indent + '\t\t}\n'
                + indent + '\t);\n'
                + "\n"
                + indent + '$main\n'
                + indent + '\t.find("#hr-leave-application")\n'
                + indent + '\t.on(\n'
                + indent + '\t\t"click",\n'
                + indent + '\t\tfunction () {\n'
                + indent + '\t\t\tfrappe.new_doc("Leave Application");\n'
                + indent + '\t\t}\n'
                + indent + '\t);\n'
                + "\n"
                + indent + '$main\n'
                + indent + '\t.find("#hr-expense-claim")\n'
                + indent + '\t.on(\n'
                + indent + '\t\t"click",\n'
                + indent + '\t\tfunction () {\n'
                + indent + '\t\t\tfrappe.new_doc("Expense Claim");\n'
                + indent + '\t\t}\n'
                + indent + '\t);\n'
            )
            lines.insert(end + 1, new_block)
            done.append("buttons_js")
        else:
            skipped.append(("buttons_js", "could not find end of #hr-refresh click handler block"))
    else:
        skipped.append(("buttons_js", '.find("#hr-refresh") not found'))

    if not done:
        print("Nothing changed.")
        sys.exit(1)

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = "%s.backup_before_actionbuttons_%s" % (path, stamp)
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
