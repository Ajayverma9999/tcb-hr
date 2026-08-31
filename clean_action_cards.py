import re
import sys
import shutil
from datetime import datetime

if len(sys.argv) != 2:
    print("Usage: python3 clean_action_cards.py /path/to/hr_console.js")
    sys.exit(1)

path = sys.argv[1]

with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# Backup
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = f"{path}.backup_before_clean_{stamp}"
shutil.copy2(path, backup)
print(f"Backup saved: {backup}")

ids = [
    "hr-wfh-apply",
    "hr-leave-application",
    "hr-expense-claim",
]

# Find complete div block for each action-card ID
def find_div_block(s, pos):
    start = s.rfind("<div", 0, pos)
    if start == -1:
        return None

    depth = 0
    for m in re.finditer(r"</?div\b[^>]*>", s[start:], re.I):
        tag = m.group(0)
        if tag.startswith("</"):
            depth -= 1
            if depth == 0:
                return start, start + m.end()
        else:
            depth += 1

    return None

# Collect existing action-card blocks
blocks = []

for card_id in ids:
    matches = list(re.finditer(
        rf'<div\b[^>]*\bid="{re.escape(card_id)}"[^>]*>',
        text,
        re.I
    ))

    if not matches:
        print(f"WARNING: {card_id} not found")
        continue

    # Keep only FIRST occurrence, remove duplicates
    first = True

    for match in matches:
        block = find_div_block(text, match.start())

        if not block:
            continue

        start, end = block

        if first:
            blocks.append((card_id, start, end))
            first = False
        else:
            # Mark duplicate for removal
            blocks.append((f"REMOVE_DUPLICATE:{card_id}", start, end))

# Remove duplicate blocks from bottom to top
for name, start, end in sorted(
    [b for b in blocks if b[0].startswith("REMOVE_DUPLICATE:")],
    key=lambda x: x[1],
    reverse=True
):
    text = text[:start] + text[end:]
    print(f"Removed duplicate: {name.split(':',1)[1]}")

# Recalculate blocks after duplicate removal
for card_id in ids:
    match = re.search(
        rf'<div\b[^>]*\bid="{re.escape(card_id)}"[^>]*>',
        text,
        re.I
    )

    if not match:
        continue

    block = find_div_block(text, match.start())
    if not block:
        continue

    start, end = block
    html = text[start:end]

    # Remove "+ Apply" action text/div
    html = re.sub(
        r'\s*<div\b[^>]*>\s*\+\s*Apply\s*</div>\s*',
        "\n",
        html,
        flags=re.I
    )

    # Also remove plain + Apply if present
    html = re.sub(r'\+\s*Apply', '', html, flags=re.I)

    text = text[:start] + html + text[end:]

    print(f"Cleaned: {card_id}")

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("\nDone.")
print("Only one card of each type remains.")
print("+ Apply removed.")
print("Existing click handlers were not changed.")
