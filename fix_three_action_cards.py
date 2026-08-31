from pathlib import Path

path = Path("tcb_customization/tcb/page/hr_console/hr_console.js")
text = path.read_text()

def find_div_end(s, start):
    depth = 0
    i = start

    while i < len(s):
        if s.startswith("<div", i):
            depth += 1
            i += 4
        elif s.startswith("</div>", i):
            depth -= 1
            i += 6
            if depth == 0:
                return i
        else:
            i += 1

    return None

cards = {
    "hr-wfh-apply": ("Work From Home", "hr-wfh-count"),
    "hr-leave-application": ("Leave Application", "hr-leave-application-count"),
    "hr-expense-claim": ("Expense Claim", "hr-expense-claim-count"),
}

for card_id, (label, count_id) in cards.items():

    marker = f'id="{card_id}"'
    pos = text.find(marker)

    if pos == -1:
        print(f"NOT FOUND: {card_id}")
        continue

    start = text.rfind("<div", 0, pos)

    if start == -1:
        print(f"START NOT FOUND: {card_id}")
        continue

    end = find_div_end(text, start)

    if end is None:
        print(f"END NOT FOUND: {card_id}")
        continue

    new_card = f'''					<div
						class="hr-stat-card hr-action-card"
						id="{card_id}"
						style="
							padding:20px;
							border:1px solid #ddd;
							border-radius:10px;
							background:white;
							cursor:pointer;
						"
					>
						<div style="color:#888;font-size:13px;">
							{label}
						</div>

						<div
							id="{count_id}"
							style="
								font-size:30px;
								font-weight:700;
								margin-top:8px;
							"
						>
							0
						</div>
					</div>'''

    text = text[:start] + new_card + text[end:]

path.write_text(text)

print("3 action cards fixed.")
print("Same UI structure as the existing summary cards.")
print("Existing click handlers were not changed.")
