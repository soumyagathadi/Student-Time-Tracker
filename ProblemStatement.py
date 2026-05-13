import csv
import os
import uuid
from datetime import date, datetime, timedelta
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class TimeTrackerApp:
	def __init__(self, root: tk.Tk) -> None:
		self.root = root
		self.root.title("Student Time Tracker")

		self.data_file = os.path.join(os.path.dirname(__file__), "time_entries.csv")
		self.entries = []
		self.selected_id = None

		self.default_tasks = [
			"Solving programming questions",
			"Studying",
			"Lectures",
			"Projects",
			"Exercise",
			"Break",
			"Social",
			"Sleep",
			"Other",
		]
		self.default_categories = [
			"Study",
			"Class",
			"Project",
			"Health",
			"Personal",
			"Rest",
			"Other",
		]

		self._build_ui()
		self.load_data()
		self.refresh_view()

	def _build_ui(self) -> None:
		self.root.columnconfigure(0, weight=1)
		self.root.rowconfigure(0, weight=1)

		main = ttk.Frame(self.root, padding=10)
		main.grid(row=0, column=0, sticky="nsew")
		main.columnconfigure(0, weight=1)
		main.columnconfigure(1, weight=3)
		main.rowconfigure(1, weight=1)

		form_frame = ttk.LabelFrame(main, text="Add / Edit Entry", padding=10)
		form_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

		self.date_var = tk.StringVar(value=date.today().isoformat())
		self.task_var = tk.StringVar()
		self.category_var = tk.StringVar(value=self.default_categories[0])
		self.hours_var = tk.StringVar(value="2")
		self.notes_var = tk.StringVar()

		ttk.Label(form_frame, text="Date (YYYY-MM-DD)").grid(row=0, column=0, sticky="w")
		ttk.Entry(form_frame, textvariable=self.date_var, width=18).grid(
			row=1, column=0, sticky="ew", pady=(0, 8)
		)

		ttk.Label(form_frame, text="Task").grid(row=2, column=0, sticky="w")
		task_box = ttk.Combobox(
			form_frame,
			textvariable=self.task_var,
			values=self.default_tasks,
		)
		task_box.grid(row=3, column=0, sticky="ew", pady=(0, 8))
		task_box.set(self.default_tasks[0])

		ttk.Label(form_frame, text="Category").grid(row=4, column=0, sticky="w")
		category_box = ttk.Combobox(
			form_frame,
			textvariable=self.category_var,
			values=self.default_categories,
		)
		category_box.grid(row=5, column=0, sticky="ew", pady=(0, 8))

		ttk.Label(form_frame, text="Hours").grid(row=6, column=0, sticky="w")
		ttk.Entry(form_frame, textvariable=self.hours_var, width=10).grid(
			row=7, column=0, sticky="ew", pady=(0, 8)
		)

		ttk.Label(form_frame, text="Notes").grid(row=8, column=0, sticky="w")
		ttk.Entry(form_frame, textvariable=self.notes_var).grid(
			row=9, column=0, sticky="ew", pady=(0, 8)
		)

		button_frame = ttk.Frame(form_frame)
		button_frame.grid(row=10, column=0, sticky="ew")
		button_frame.columnconfigure(0, weight=1)
		button_frame.columnconfigure(1, weight=1)

		ttk.Button(button_frame, text="Add", command=self.add_entry).grid(
			row=0, column=0, sticky="ew", padx=(0, 6)
		)
		ttk.Button(button_frame, text="Update", command=self.update_entry).grid(
			row=0, column=1, sticky="ew"
		)
		ttk.Button(button_frame, text="Delete", command=self.delete_entry).grid(
			row=1, column=0, sticky="ew", pady=(6, 0), padx=(0, 6)
		)
		ttk.Button(button_frame, text="Clear", command=self.clear_form).grid(
			row=1, column=1, sticky="ew", pady=(6, 0)
		)
		ttk.Button(button_frame, text="Quick Add 2h Programming", command=self.quick_add_programming).grid(
			row=2, column=0, columnspan=2, sticky="ew", pady=(6, 0)
		)

		list_frame = ttk.LabelFrame(main, text="Entries", padding=10)
		list_frame.grid(row=0, column=1, sticky="nsew")
		list_frame.rowconfigure(0, weight=1)
		list_frame.columnconfigure(0, weight=1)

		columns = ("date", "task", "category", "hours", "notes")
		self.tree = ttk.Treeview(
			list_frame,
			columns=columns,
			show="headings",
			height=10,
		)
		self.tree.grid(row=0, column=0, sticky="nsew")

		for col, label, width in [
			("date", "Date", 110),
			("task", "Task", 220),
			("category", "Category", 120),
			("hours", "Hours", 60),
			("notes", "Notes", 220),
		]:
			self.tree.heading(col, text=label)
			self.tree.column(col, width=width, anchor="w")

		scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
		scrollbar.grid(row=0, column=1, sticky="ns")
		self.tree.configure(yscrollcommand=scrollbar.set)
		self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

		action_frame = ttk.Frame(list_frame)
		action_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
		action_frame.columnconfigure(0, weight=1)
		action_frame.columnconfigure(1, weight=1)
		action_frame.columnconfigure(2, weight=1)

		ttk.Button(action_frame, text="Import CSV", command=self.import_csv).grid(
			row=0, column=0, sticky="ew", padx=(0, 6)
		)
		ttk.Button(action_frame, text="Export CSV", command=self.export_csv).grid(
			row=0, column=1, sticky="ew", padx=(0, 6)
		)
		ttk.Button(action_frame, text="Save", command=self.save_data).grid(
			row=0, column=2, sticky="ew"
		)

		insights_frame = ttk.LabelFrame(main, text="Insights", padding=10)
		insights_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(10, 0))
		insights_frame.columnconfigure(0, weight=1)
		insights_frame.columnconfigure(1, weight=1)

		self.summary_var = tk.StringVar()
		summary_label = ttk.Label(insights_frame, textvariable=self.summary_var, justify="left")
		summary_label.grid(row=0, column=0, sticky="nw")

		self.target_task_var = tk.StringVar(value="Solving programming questions")
		self.target_hours_var = tk.StringVar(value="2")
		self.target_progress_var = tk.DoubleVar(value=0.0)
		self.target_status_var = tk.StringVar()

		target_frame = ttk.LabelFrame(insights_frame, text="Daily Target", padding=8)
		target_frame.grid(row=1, column=0, sticky="ew", pady=(8, 0))
		target_frame.columnconfigure(1, weight=1)

		ttk.Label(target_frame, text="Task").grid(row=0, column=0, sticky="w")
		target_task_box = ttk.Combobox(
			target_frame,
			textvariable=self.target_task_var,
			values=self.default_tasks,
		)
		target_task_box.grid(row=0, column=1, sticky="ew", padx=(6, 0))

		ttk.Label(target_frame, text="Target hours").grid(row=1, column=0, sticky="w", pady=(6, 0))
		ttk.Entry(target_frame, textvariable=self.target_hours_var, width=8).grid(
			row=1, column=1, sticky="w", padx=(6, 0), pady=(6, 0)
		)

		self.target_progress = ttk.Progressbar(
			target_frame,
			variable=self.target_progress_var,
			maximum=100,
		)
		self.target_progress.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 2))

		ttk.Label(target_frame, textvariable=self.target_status_var).grid(
			row=3, column=0, columnspan=2, sticky="w"
		)

		chart_frame = ttk.Frame(insights_frame)
		chart_frame.grid(row=0, column=1, sticky="nsew")
		chart_frame.columnconfigure(0, weight=1)
		chart_frame.rowconfigure(0, weight=1)
		chart_frame.rowconfigure(1, weight=1)

		self.category_chart = tk.Canvas(chart_frame, width=380, height=160, bg="white")
		self.category_chart.grid(row=0, column=0, sticky="nsew", pady=(0, 8))

		self.week_chart = tk.Canvas(chart_frame, width=380, height=160, bg="white")
		self.week_chart.grid(row=1, column=0, sticky="nsew")

		self.target_task_var.trace_add("write", lambda *_: self.refresh_summary())
		self.target_hours_var.trace_add("write", lambda *_: self.refresh_summary())

	def load_data(self) -> None:
		if not os.path.exists(self.data_file):
			self.entries = [self._make_default_entry()]
			self.save_data()
			return

		with open(self.data_file, "r", newline="", encoding="utf-8") as file:
			reader = csv.DictReader(file)
			self.entries = []
			for row in reader:
				if not row:
					continue
				entry_id = row.get("id") or str(uuid.uuid4())
				self.entries.append(
					{
						"id": entry_id,
						"date": row.get("date", ""),
						"task": row.get("task", ""),
						"category": row.get("category", ""),
						"hours": row.get("hours", ""),
						"notes": row.get("notes", ""),
					}
				)

		if not self.entries:
			self.entries = [self._make_default_entry()]
			self.save_data()

	def save_data(self) -> None:
		with open(self.data_file, "w", newline="", encoding="utf-8") as file:
			fieldnames = ["id", "date", "task", "category", "hours", "notes"]
			writer = csv.DictWriter(file, fieldnames=fieldnames)
			writer.writeheader()
			for entry in self.entries:
				writer.writerow(entry)

	def _make_default_entry(self) -> dict:
		return {
			"id": str(uuid.uuid4()),
			"date": date.today().isoformat(),
			"task": "Solving programming questions",
			"category": "Study",
			"hours": "2",
			"notes": "Default sample task",
		}

	def validate_entry(self) -> bool:
		try:
			datetime.fromisoformat(self.date_var.get().strip())
		except ValueError:
			messagebox.showerror("Invalid Date", "Use YYYY-MM-DD format.")
			return False

		try:
			hours_value = float(self.hours_var.get().strip())
			if hours_value <= 0:
				raise ValueError
		except ValueError:
			messagebox.showerror("Invalid Hours", "Hours must be a number greater than 0.")
			return False

		if not self.task_var.get().strip():
			messagebox.showerror("Missing Task", "Please enter a task name.")
			return False

		return True

	def add_entry(self) -> None:
		if not self.validate_entry():
			return

		entry = {
			"id": str(uuid.uuid4()),
			"date": self.date_var.get().strip(),
			"task": self.task_var.get().strip(),
			"category": self.category_var.get().strip(),
			"hours": self.hours_var.get().strip(),
			"notes": self.notes_var.get().strip(),
		}
		self.entries.append(entry)
		self.clear_form()
		self.refresh_view()

	def update_entry(self) -> None:
		if not self.selected_id:
			messagebox.showinfo("Select Entry", "Choose an entry to update.")
			return
		if not self.validate_entry():
			return

		for entry in self.entries:
			if entry["id"] == self.selected_id:
				entry.update(
					{
						"date": self.date_var.get().strip(),
						"task": self.task_var.get().strip(),
						"category": self.category_var.get().strip(),
						"hours": self.hours_var.get().strip(),
						"notes": self.notes_var.get().strip(),
					}
				)
				break
		self.refresh_view()

	def delete_entry(self) -> None:
		if not self.selected_id:
			messagebox.showinfo("Select Entry", "Choose an entry to delete.")
			return
		self.entries = [e for e in self.entries if e["id"] != self.selected_id]
		self.selected_id = None
		self.clear_form()
		self.refresh_view()

	def clear_form(self) -> None:
		self.date_var.set(date.today().isoformat())
		self.task_var.set(self.default_tasks[0])
		self.category_var.set(self.default_categories[0])
		self.hours_var.set("2")
		self.notes_var.set("")
		self.selected_id = None

	def quick_add_programming(self) -> None:
		self.date_var.set(date.today().isoformat())
		self.task_var.set("Solving programming questions")
		self.category_var.set("Study")
		self.hours_var.set("2")
		self.notes_var.set("Focused practice")
		self.add_entry()

	def on_tree_select(self, _event: tk.Event) -> None:
		selection = self.tree.selection()
		if not selection:
			return
		item_id = selection[0]
		self.selected_id = item_id
		entry = next((e for e in self.entries if e["id"] == item_id), None)
		if not entry:
			return
		self.date_var.set(entry.get("date", ""))
		self.task_var.set(entry.get("task", ""))
		self.category_var.set(entry.get("category", ""))
		self.hours_var.set(entry.get("hours", ""))
		self.notes_var.set(entry.get("notes", ""))

	def import_csv(self) -> None:
		file_path = filedialog.askopenfilename(
			title="Import CSV",
			filetypes=[("CSV Files", "*.csv")],
		)
		if not file_path:
			return

		imported = 0
		with open(file_path, "r", newline="", encoding="utf-8") as file:
			reader = csv.DictReader(file)
			for row in reader:
				if not row:
					continue
				self.entries.append(
					{
						"id": str(uuid.uuid4()),
						"date": row.get("date", ""),
						"task": row.get("task", ""),
						"category": row.get("category", ""),
						"hours": row.get("hours", ""),
						"notes": row.get("notes", ""),
					}
				)
				imported += 1

		if imported:
			self.refresh_view()
			messagebox.showinfo("Import Complete", f"Imported {imported} entries.")

	def export_csv(self) -> None:
		file_path = filedialog.asksaveasfilename(
			title="Export CSV",
			defaultextension=".csv",
			filetypes=[("CSV Files", "*.csv")],
		)
		if not file_path:
			return

		with open(file_path, "w", newline="", encoding="utf-8") as file:
			fieldnames = ["date", "task", "category", "hours", "notes"]
			writer = csv.DictWriter(file, fieldnames=fieldnames)
			writer.writeheader()
			for entry in self.entries:
				writer.writerow(
					{
						"date": entry.get("date", ""),
						"task": entry.get("task", ""),
						"category": entry.get("category", ""),
						"hours": entry.get("hours", ""),
						"notes": entry.get("notes", ""),
					}
				)

		messagebox.showinfo("Export Complete", "CSV exported successfully.")

	def refresh_view(self) -> None:
		for item in self.tree.get_children():
			self.tree.delete(item)
		for entry in self.entries:
			self.tree.insert(
				"",
				tk.END,
				iid=entry["id"],
				values=(
					entry.get("date", ""),
					entry.get("task", ""),
					entry.get("category", ""),
					entry.get("hours", ""),
					entry.get("notes", ""),
				),
			)

		self.refresh_summary()
		self.save_data()

	def refresh_summary(self) -> None:
		today = date.today()
		week_start = today - timedelta(days=6)

		totals_today = 0.0
		totals_week = 0.0
		category_totals = {}
		task_totals = {}
		daily_totals = {}

		for entry in self.entries:
			entry_date = self._parse_date(entry.get("date", ""))
			hours = self._parse_hours(entry.get("hours", ""))
			if not entry_date:
				continue

			if entry_date == today:
				totals_today += hours
			if week_start <= entry_date <= today:
				totals_week += hours
				day_key = entry_date.isoformat()
				daily_totals[day_key] = daily_totals.get(day_key, 0.0) + hours

			category = entry.get("category", "Other") or "Other"
			task = entry.get("task", "Other") or "Other"
			category_totals[category] = category_totals.get(category, 0.0) + hours
			task_totals[task] = task_totals.get(task, 0.0) + hours

		top_category = self._top_key(category_totals)
		top_task = self._top_key(task_totals)
		avg_daily = totals_week / 7 if totals_week else 0.0

		target_task = self.target_task_var.get().strip()
		target_hours = self._parse_hours(self.target_hours_var.get().strip())
		target_today_hours = 0.0
		if target_task:
			for entry in self.entries:
				entry_date = self._parse_date(entry.get("date", ""))
				if entry_date != today:
					continue
				if entry.get("task", "").strip() == target_task:
					target_today_hours += self._parse_hours(entry.get("hours", ""))

		if target_hours > 0:
			progress = min(100.0, (target_today_hours / target_hours) * 100.0)
			self.target_progress_var.set(progress)
			self.target_status_var.set(
				f"{target_today_hours:.1f} / {target_hours:.1f} hours today"
			)
		else:
			self.target_progress_var.set(0.0)
			self.target_status_var.set("Set a target greater than 0")

		summary_lines = [
			f"Today: {totals_today:.1f} hours",
			f"Last 7 days: {totals_week:.1f} hours",
			f"Average per day (7d): {avg_daily:.1f} hours",
		]
		if top_category:
			summary_lines.append(f"Top category: {top_category}")
		if top_task:
			summary_lines.append(f"Top task: {top_task}")
		self.summary_var.set("\n".join(summary_lines))

		category_view = dict(sorted(category_totals.items(), key=lambda item: item[1], reverse=True)[:6])
		last_7_days = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
		week_view = {
			day.strftime("%a"): daily_totals.get(day.isoformat(), 0.0)
			for day in last_7_days
		}

		self._draw_bar_chart(
			self.category_chart,
			category_view,
			"Hours by Category",
			"#4a7a8c",
		)
		self._draw_bar_chart(
			self.week_chart,
			week_view,
			"Last 7 Days",
			"#9a6b3f",
		)

	@staticmethod
	def _parse_date(value: str) -> date | None:
		try:
			return datetime.fromisoformat(value).date()
		except ValueError:
			return None

	@staticmethod
	def _parse_hours(value: str) -> float:
		try:
			return float(value)
		except (TypeError, ValueError):
			return 0.0

	@staticmethod
	def _top_key(totals: dict) -> str:
		if not totals:
			return ""
		return max(totals.items(), key=lambda item: item[1])[0]

	def _draw_bar_chart(self, canvas: tk.Canvas, data: dict, title: str, color: str) -> None:
		canvas.delete("all")
		width = int(canvas["width"])
		height = int(canvas["height"])
		padding = 30

		canvas.create_text(padding, 10, text=title, anchor="nw", font=("TkDefaultFont", 10, "bold"))

		if not data or max(data.values()) == 0:
			canvas.create_text(width / 2, height / 2, text="No data yet", fill="gray")
			return

		max_value = max(data.values())
		bar_area_height = height - 50
		bar_width = max(20, int((width - 2 * padding) / max(1, len(data)) - 10))
		x = padding

		for label, value in data.items():
			bar_height = (value / max_value) * bar_area_height
			y0 = height - 20 - bar_height
			y1 = height - 20
			canvas.create_rectangle(x, y0, x + bar_width, y1, fill=color, outline="")
			canvas.create_text(x + bar_width / 2, y0 - 8, text=f"{value:.1f}", font=("TkDefaultFont", 8))
			short_label = label if len(label) <= 8 else f"{label[:8]}..."
			canvas.create_text(
				x + bar_width / 2,
				y1 + 10,
				text=short_label,
				font=("TkDefaultFont", 8),
			)
			x += bar_width + 10


def main() -> None:
	root = tk.Tk()
	app = TimeTrackerApp(root)
	root.mainloop()


if __name__ == "__main__":
	main()
