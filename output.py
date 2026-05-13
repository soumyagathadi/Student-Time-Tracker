import csv
import os
import textwrap
from datetime import date, datetime, timedelta


OUTER_WIDTH = 78
OUTER_INNER = OUTER_WIDTH - 2
INDENT = 2
BOX_WIDTH = OUTER_INNER - (INDENT * 2)


def load_entries(csv_path: str) -> list[dict]:
	if not os.path.exists(csv_path):
		return []
	entries = []
	with open(csv_path, "r", newline="", encoding="utf-8") as file:
		reader = csv.DictReader(file)
		for row in reader:
			if not row:
				continue
			entries.append(row)
	return entries


def parse_date(value: str) -> date | None:
	try:
		return datetime.fromisoformat(value).date()
	except ValueError:
		return None


def parse_hours(value: str) -> float:
	try:
		return float(value)
	except (TypeError, ValueError):
		return 0.0


def top_key(totals: dict[str, float]) -> str:
	if not totals:
		return ""
	return max(totals.items(), key=lambda item: item[1])[0]


def make_bar(value: float, max_value: float, width: int = 12) -> str:
	if max_value <= 0:
		return "".ljust(width)
	filled = int(round((value / max_value) * width))
	return "#" * min(width, max(0, filled)) + " " * max(0, width - filled)


def format_line(text: str) -> str:
	return "|" + text.ljust(OUTER_INNER)[:OUTER_INNER] + "|"


def render_box(title: str, lines: list[str]) -> list[str]:
	border = " " * INDENT + "+" + "-" * BOX_WIDTH + "+"
	content = [border]
	content.append(" " * INDENT + "|" + f" {title}".ljust(BOX_WIDTH) + "|")
	content.append(border)
	for line in lines:
		content.append(" " * INDENT + "|" + line.ljust(BOX_WIDTH)[:BOX_WIDTH] + "|")
	content.append(border)
	return content


def wrap_labeled_line(label: str, value: str, width: int) -> list[str]:
	prefix = f"{label}: "
	wrapper = textwrap.TextWrapper(width=width, subsequent_indent=" " * len(prefix))
	return wrapper.wrap(prefix + value)


def build_dashboard_preview(
	total_hours: float,
	total_entries: int,
	week_hours: float,
	category_totals: dict[str, float],
	week_view: dict[str, float],
) -> list[str]:
	lines: list[str] = []
	lines.append("Student Time Tracker")
	lines.append("")
	lines.append(f"Total Hours: {total_hours:.1f}    Entries: {total_entries}")
	lines.append(f"Last 7 Days: {week_hours:.1f}     Avg/Day: {week_hours / 7:.1f}")
	lines.append("")

	left_width = 32
	left_title = "Time by Category"
	right_title = "Last 7 Days"
	lines.append(f"{left_title.ljust(left_width)} | {right_title}")

	max_category = max(category_totals.values()) if category_totals else 0.0
	category_items = sorted(category_totals.items(), key=lambda item: item[1], reverse=True)[:5]
	category_rows = []
	for name, value in category_items:
		label = name[:10].ljust(10)
		bar = make_bar(value, max_category)
		category_rows.append(f"{label} {bar} {value:4.1f}")

	max_week = max(week_view.values()) if week_view else 0.0
	week_rows = []
	for day, value in week_view.items():
		bar = make_bar(value, max_week, width=10)
		week_rows.append(f"{day} {bar} {value:4.1f}")

	row_count = max(len(category_rows), len(week_rows))
	if row_count == 0:
		lines.append("No tracking data yet.")
		return lines

	for idx in range(row_count):
		left = category_rows[idx] if idx < len(category_rows) else ""
		right = week_rows[idx] if idx < len(week_rows) else ""
		lines.append(f"{left.ljust(left_width)} | {right}")

	return lines


def main() -> None:
	data_file = os.path.join(os.path.dirname(__file__), "time_entries.csv")
	entries = load_entries(data_file)

	today = date.today()
	week_start = today - timedelta(days=6)

	category_totals: dict[str, float] = {}
	task_totals: dict[str, float] = {}
	week_totals: dict[str, float] = { (today - timedelta(days=i)).strftime("%a"): 0.0 for i in range(6, -1, -1) }

	total_hours = 0.0
	week_hours = 0.0
	programming_week = 0.0

	for entry in entries:
		entry_date = parse_date(entry.get("date", ""))
		hours = parse_hours(entry.get("hours", ""))
		if not entry_date:
			continue

		total_hours += hours
		category = entry.get("category", "Other") or "Other"
		task = entry.get("task", "Other") or "Other"
		category_totals[category] = category_totals.get(category, 0.0) + hours
		task_totals[task] = task_totals.get(task, 0.0) + hours

		if week_start <= entry_date <= today:
			week_hours += hours
			week_key = entry_date.strftime("%a")
			if week_key in week_totals:
				week_totals[week_key] += hours
			if task.strip().lower() == "solving programming questions":
				programming_week += hours

	if not entries:
		category_totals = {"Study": 2.0, "Class": 1.5, "Rest": 1.0}
		task_totals = {"Solving programming questions": 2.0, "Lectures": 1.5}
		week_totals = { (today - timedelta(days=i)).strftime("%a"): 0.0 for i in range(6, -1, -1) }
		week_totals[today.strftime("%a")] = 2.0
		total_hours = 2.0
		week_hours = 2.0
		programming_week = 2.0

	top_category = top_key(category_totals)
	top_task = top_key(task_totals)

	insights = []
	if top_category:
		insights.append(f"Top category this week: {top_category} ({category_totals[top_category]:.1f}h).")
	if top_task:
		insights.append(f"Top task overall: {top_task} ({task_totals[top_task]:.1f}h).")
	if programming_week:
		insights.append(f"Programming practice this week: {programming_week:.1f}h.")
	insights.append(f"Average tracked per day (7d): {week_hours / 7:.1f}h.")

	sections: list[str] = []
	sections.extend(render_box("MY DATA SCIENCE PROJECT: WHAT I BUILT THIS WEEK", []))
	sections.append("")

	overview_lines = [
		"Name: Student Time Tracker",
		*wrap_labeled_line(
			"Problem",
			"I often felt busy but could not see where my study time was actually going.",
			BOX_WIDTH,
		),
		"Solution: Desktop app that logs tasks and summarizes time patterns.",
		"Timeline: 7 days",
		"Tech: Python, Tkinter, CSV, basic analytics",
	]
	sections.extend(render_box("PROJECT OVERVIEW", overview_lines))
	sections.append("")

	dashboard_lines = build_dashboard_preview(
		total_hours,
		len(entries),
		week_hours,
		category_totals,
		week_totals,
	)
	sections.extend(render_box("DASHBOARD PREVIEW", dashboard_lines))
	sections.append("")

	sections.extend(render_box("KEY INSIGHTS DISCOVERED", [f"- {line}" for line in insights]))
	sections.append("")

	learned_lines = [
		"- Real-world data needs cleaning and consistent categories.",
		"- Visual summaries make patterns obvious.",
		"- Small daily logging builds better habits.",
		"- Building for myself kept me motivated.",
	]
	sections.extend(render_box("WHAT I LEARNED", learned_lines))
	sections.append("")

	feedback_lines = [
		"\"This makes it easier to see my study balance.\"",
		"  - Friend",
		"\"The daily target bar is a great motivator.\"",
		"  - Classmate",
	]
	sections.extend(render_box("FEEDBACK RECEIVED", feedback_lines))
	sections.append("")

	links_lines = [
		"Live Demo: (local Tkinter app)",
		"Source Code: (https://github.com/soumyagathadi/Student-Time-Tracker)",
		
	]
	sections.extend(render_box("LINKS", links_lines))
	sections.append("")
	sections.append(" [ GitHub ] [User Guide] ")
	

	print("+" + "-" * OUTER_INNER + "+")
	for line in sections:
		print(format_line(line))
	print("+" + "-" * OUTER_INNER + "+")


if __name__ == "__main__":
	main()
