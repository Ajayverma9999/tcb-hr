#!/usr/bin/env python3
import sys
import shutil
import datetime

def stripped(s):
    return s.strip()

def find_div_block_end(lines, start):
    """Given start index of an opening '<div' line, find index of its matching '</div>' line."""
    depth = 0
    for j in range(start, len(lines)):
        depth += lines[j].count("<div") - lines[j].count("</div>")
        if depth == 0 and j > start:
            return j
    return None

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 fix_action_cards.py /path/to/hr_console.js")
        sys.exit(1)

    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    done = []
    skipped = []

    # ---- 1. Remove old 3 <button> blocks ----
    idx_wfh_btn = None
    idx_expense_btn = None
    for i, l in enumerate(lines):
        if stripped(l) == 'id="hr-wfh-apply"':
            idx_wfh_btn = i
        if stripped(l) == 'id="hr-expense-claim"':
            idx_expense_btn = i

    if idx_wfh_btn is not None and idx_expense_btn is not None:
        start = None
        for j in range(idx_wfh_btn, max(idx_wfh_btn - 5, -1), -1):
            if stripped(lines[j]) == "<button":
                start = j
                break
        end = None
        for j in range(idx_expense_btn, min(idx_expense_btn + 6, len(lines))):
            if stripped(lines[j]) == "</button>":
                end = j
                break
        if start is not None and end is not None:
            del lines[start:end + 1]
            done.append("remove_old_buttons_html")
        else:
            skipped.append(("remove_old_buttons_html", "boundaries not found"))
    else:
        skipped.append(("remove_old_buttons_html", "already removed or ids not found"))

    # ---- 2. Remove old JS click handlers (3 blocks, contiguous, ending right before "// REVIEW") ----
    idx_wfh_find = None
    idx_review_comment = None
    for i, l in enumerate(lines):
        if '.find("#hr-wfh-apply")' in l:
            idx_wfh_find = i
        if stripped(l) == "// REVIEW":
            idx_review_comment = i
    if idx_wfh_find is not None and idx_review_comment is not None:
        start = idx_wfh_find - 1  # the "$main" line right before
        end = idx_review_comment - 2  # the ");" line right before the separator comment
        if stripped(lines[start]) == "$main" and end > start:
            del lines[start:end + 1]
            done.append("remove_old_buttons_js")
        else:
            skipped.append(("remove_old_buttons_js", "boundary lines did not match expected pattern"))
    else:
        skipped.append(("remove_old_buttons_js", "handlers already removed or markers not found"))

    # ---- 3. Insert 3 new card-style boxes into the summary grid, after the "On Leave" card ----
    idx_onleave = None
    for i, l in enumerate(lines):
        if stripped(l) == 'data-status="On Leave"':
            idx_onleave = i
            break
    if idx_onleave is not None:
        card_start = None
        for j in range(idx_onleave, max(idx_onleave - 5, -1), -1):
            if stripped(lines[j]) == "<div":
                card_start = j
                break
        if card_start is not None:
            card_end = find_div_block_end(lines, card_start)
            if card_end is not None:
                indent = lines[card_start][:len(lines[card_start]) - len(lines[card_start].lstrip("\t"))]
                def card(card_id, label, action_text):
                    return (
                        indent + '<div\n'
                        + indent + '\tclass="hr-stat-card hr-action-card"\n'
                        + indent + '\tid="' + card_id + '"\n'
                        + indent + '\tstyle="\n'
                        + indent + '\t\tpadding:20px;\n'
                        + indent + '\t\tborder:1px solid #ddd;\n'
                        + indent + '\t\tborder-radius:10px;\n'
                        + indent + '\t\tbackground:white;\n'
                        + indent + '\t\tcursor:pointer;\n'
                        + indent + '\t"\n'
                        + indent + '>\n'
                        + indent + '\t<div style="color:#888;font-size:13px;">\n'
                        + indent + '\t\t' + label + '\n'
                        + indent + '\t</div>\n'
                        + indent + '\t<div\n'
                        + indent + '\t\tstyle="\n'
                        + indent + '\t\t\tfont-size:18px;\n'
                        + indent + '\t\t\tfont-weight:700;\n'
                        + indent + '\t\t\tmargin-top:8px;\n'
                        + indent + '\t\t\tcolor:#2563eb;\n'
                        + indent + '\t\t"\n'
                        + indent + '\t>\n'
                        + indent + '\t\t' + action_text + '\n'
                        + indent + '\t</div>\n'
                        + indent + '</div>\n'
                    )
                new_block = (
                    card("hr-wfh-apply", "Work From Home", "+ Apply")
                    + card("hr-leave-application", "Leave Application", "+ Apply")
                    + card("hr-expense-claim", "Expense Claim", "+ Apply")
                )
                lines.insert(card_end + 1, new_block)
                done.append("insert_cards")
            else:
                skipped.append(("insert_cards", "could not find end of On Leave card block"))
        else:
            skipped.append(("insert_cards", "could not find start of On Leave card block"))
    else:
        skipped.append(("insert_cards", 'data-status="On Leave" not found'))

    # ---- 4. Update the CARD CLICK filter handler to exclude .hr-action-card ----
    idx_cardclick = None
    for i, l in enumerate(lines):
        if stripped(l) == '.find(".hr-stat-card")':
            idx_cardclick = i
            break
    if idx_cardclick is not None:
        next_line = lines[idx_cardclick + 1] if idx_cardclick + 1 < len(lines) else ""
        if stripped(next_line) == ".on(":
            indent = lines[idx_cardclick][:len(lines[idx_cardclick]) - len(lines[idx_cardclick].lstrip("\t"))]
            insert_line = indent + '.not(".hr-action-card")\n'
            lines.insert(idx_cardclick + 1, insert_line)
            done.append("filter_handler_updated")
        else:
            skipped.append(("filter_handler_updated", "unexpected structure after .find('.hr-stat-card')"))
    else:
        skipped.append(("filter_handler_updated", '.find(".hr-stat-card") not found'))

    # ---- 5. Add fresh click handlers for the 3 action cards, right after the CARD CLICK handler block ----
    idx_cardclick2 = None
    for i, l in enumerate(lines):
        if '.find(".hr-stat-card")' in l and (i + 1 < len(lines)) and '.not(".hr-action-card")' in lines[i + 1]:
            idx_cardclick2 = i
            break
    if idx_cardclick2 is not None:
        # find end of this handler: depth-based scan for matching ");" after the function body
        depth = 0
        started = False
        func_closed_at = None
        for j in range(idx_cardclick2, len(lines)):
            depth += lines[j].count("{") - lines[j].count("}")
            if "function" in lines[j]:
                started = True
            if started and depth <= 0 and j > idx_cardclick2:
                func_closed_at = j
                break
        end = None
        if func_closed_at is not None:
            for k in range(func_closed_at, min(func_closed_at + 5, len(lines))):
                if stripped(lines[k]) == ");":
                    end = k
                    break
        if end is not None:
            indent = "\t\t"
            def handler(card_id, doctype, extra_args=""):
                if extra_args:
                    body = (
                        indent + '\t\t\tfrappe.new_doc(\n'
                        + indent + '\t\t\t\t"' + doctype + '",\n'
                        + indent + '\t\t\t\t' + extra_args + '\n'
                        + indent + '\t\t\t);\n'
                    )
                else:
                    body = indent + '\t\t\tfrappe.new_doc("' + doctype + '");\n'
                return (
                    "\n"
                    + indent + '$main\n'
                    + indent + '\t.find("#' + card_id + '")\n'
                    + indent + '\t.on(\n'
                    + indent + '\t\t"click",\n'
                    + indent + '\t\tfunction () {\n'
                    + body
                    + indent + '\t\t}\n'
                    + indent + '\t);\n'
                )
            new_block = (
                handler("hr-wfh-apply", "Attendance Request", '{ reason: "Work From Home" }')
                + handler("hr-leave-application", "Leave Application")
                + handler("hr-expense-claim", "Expense Claim")
            )
            lines.insert(end + 1, new_block)
            done.append("new_click_handlers")
        else:
            skipped.append(("new_click_handlers", "could not find end of CARD CLICK handler"))
    else:
        skipped.append(("new_click_handlers", "CARD CLICK handler with .not() not found"))

    if not done:
        print("Nothing changed.")
        sys.exit(1)

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = "%s.backup_before_cardstyle_%s" % (path, stamp)
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
