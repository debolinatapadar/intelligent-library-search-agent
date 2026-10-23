"""Tkinter GUI for the Intelligent Library Search and Book Collection Agent."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, List

from library_agent import LibraryGraph


class LibraryApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Intelligent Library Search & Collection Agent")
        self.geometry("1280x800")
        self.minsize(1050, 680)
        self.model = LibraryGraph()
        self.book_vars: Dict[str, tk.BooleanVar] = {}
        self._build_style()
        self._build_ui()
        self.draw_map([])

    def _build_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), foreground="#17324d")
        style.configure("Section.TLabel", font=("Segoe UI", 11, "bold"), foreground="#17324d")
        style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), padding=7)

    def _build_ui(self) -> None:
        header = ttk.Frame(self, padding=(18, 14, 18, 8))
        header.pack(fill="x")
        ttk.Label(header, text="Intelligent Library Search & Book Collection Agent", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="Graph search + A* route optimization for collecting multiple books", foreground="#52677a").pack(anchor="w", pady=(3, 0))

        main = ttk.PanedWindow(self, orient="horizontal")
        main.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        controls = ttk.Frame(main, padding=10)
        output = ttk.Frame(main, padding=10)
        main.add(controls, weight=0)
        main.add(output, weight=1)
        self._build_controls(controls)
        self._build_output(output)

    def _build_controls(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="1. Search a book", style="Section.TLabel").pack(anchor="w")
        search_row = ttk.Frame(parent)
        search_row.pack(fill="x", pady=(6, 4))
        self.search_book = ttk.Combobox(search_row, values=list(self.model.books), state="readonly", width=27)
        self.search_book.current(0)
        self.search_book.pack(side="left", fill="x", expand=True)
        self.search_algorithm = ttk.Combobox(search_row, values=["BFS", "DFS"], state="readonly", width=6)
        self.search_algorithm.set("BFS")
        self.search_algorithm.pack(side="left", padx=(5, 0))
        ttk.Button(parent, text="Find book location", command=self.find_book).pack(fill="x", pady=(0, 12))

        ttk.Separator(parent).pack(fill="x", pady=3)
        ttk.Label(parent, text="2. Choose books for A* route", style="Section.TLabel").pack(anchor="w", pady=(10, 3))
        book_box = ttk.Frame(parent)
        book_box.pack(fill="both", expand=False)
        for title in self.model.books:
            variable = tk.BooleanVar(value=False)
            self.book_vars[title] = variable
            ttk.Checkbutton(book_box, text=title, variable=variable).pack(anchor="w", pady=1)

        settings = ttk.LabelFrame(parent, text="Route settings", padding=8)
        settings.pack(fill="x", pady=(12, 8))
        ttk.Label(settings, text="Start node").grid(row=0, column=0, sticky="w", pady=2)
        self.start_node = ttk.Combobox(settings, values=list(self.model.nodes), state="readonly", width=23)
        self.start_node.set("Entrance")
        self.start_node.grid(row=0, column=1, sticky="ew", pady=2)
        ttk.Label(settings, text="Time limit").grid(row=1, column=0, sticky="w", pady=2)
        self.time_limit = ttk.Entry(settings, width=25)
        self.time_limit.insert(0, "")
        self.time_limit.grid(row=1, column=1, sticky="ew", pady=2)
        ttk.Label(settings, text="Priority weight").grid(row=2, column=0, sticky="w", pady=2)
        self.priority_weight = ttk.Entry(settings, width=25)
        self.priority_weight.insert(0, "1.0")
        self.priority_weight.grid(row=2, column=1, sticky="ew", pady=2)
        self.accessible_only = tk.BooleanVar(value=False)
        ttk.Checkbutton(settings, text="Accessible route only", variable=self.accessible_only).grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 0))
        settings.columnconfigure(1, weight=1)
        ttk.Button(parent, text="Plan multi-book route with A*", style="Action.TButton", command=self.plan_route).pack(fill="x", pady=(0, 10))

        ttk.Label(parent, text="3. Library conditions", style="Section.TLabel").pack(anchor="w")
        conditions = ttk.Frame(parent)
        conditions.pack(fill="both", expand=True, pady=(5, 0))
        self.closed_listbox = self._listbox_group(conditions, "Closed sections", sorted(self.model.sections), 0, 0)
        self.crowded_listbox = self._listbox_group(conditions, "Crowded aisles", sorted(self.model.sections), 0, 1)
        self.unavailable_listbox = self._listbox_group(conditions, "Unavailable books", list(self.model.books), 1, 0)
        shelves = [node for node in self.model.nodes if "Shelf" in node]
        self.restricted_listbox = self._listbox_group(conditions, "Restricted shelves", shelves, 1, 1)
        conditions.columnconfigure(0, weight=1)
        conditions.columnconfigure(1, weight=1)
        conditions.rowconfigure(0, weight=1)
        conditions.rowconfigure(1, weight=1)
        ttk.Button(parent, text="Clear all conditions", command=self.clear_conditions).pack(fill="x", pady=(8, 0))

    def _listbox_group(self, parent: ttk.Frame, label: str, values: List[str], row: int, column: int) -> tk.Listbox:
        frame = ttk.LabelFrame(parent, text=label, padding=4)
        frame.grid(row=row, column=column, sticky="nsew", padx=(0 if column == 0 else 4, 4 if column == 0 else 0), pady=(0 if row == 0 else 4, 4 if row == 0 else 0))
        listbox = tk.Listbox(frame, selectmode="multiple", height=5, exportselection=False, font=("Segoe UI", 8))
        listbox.pack(fill="both", expand=True)
        for value in values:
            listbox.insert("end", value)
        return listbox

    def _build_output(self, parent: ttk.Frame) -> None:
        notebook = ttk.Notebook(parent)
        notebook.pack(fill="both", expand=True)
        map_frame = ttk.Frame(notebook)
        result_frame = ttk.Frame(notebook)
        notebook.add(map_frame, text="Library map")
        notebook.add(result_frame, text="Search and route details")
        self.canvas = tk.Canvas(map_frame, background="#f7fafc", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.result_text = tk.Text(result_frame, wrap="word", font=("Consolas", 10), background="#101820", foreground="#e6edf3", padx=14, pady=14)
        self.result_text.pack(fill="both", expand=True)
        self.write_result("Welcome! Select a search algorithm or choose books and press the A* route button.")

    def selected_conditions(self) -> dict:
        return {
            "closed_sections": [self.closed_listbox.get(i) for i in self.closed_listbox.curselection()],
            "crowded_aisles": [self.crowded_listbox.get(i) for i in self.crowded_listbox.curselection()],
            "unavailable_books": [self.unavailable_listbox.get(i) for i in self.unavailable_listbox.curselection()],
            "restricted_shelves": [self.restricted_listbox.get(i) for i in self.restricted_listbox.curselection()],
            "accessible_only": self.accessible_only.get(),
        }

    def apply_conditions(self) -> None:
        conditions = self.selected_conditions()
        self.model.set_disruptions(**conditions)
        try:
            self.model.priority_weight = max(0.0, float(self.priority_weight.get() or 0))
        except ValueError:
            self.model.priority_weight = 1.0

    def find_book(self) -> None:
        self.apply_conditions()
        title = self.search_book.get()
        algorithm = self.search_algorithm.get()
        result = self.model.bfs_or_dfs(title, algorithm, self.start_node.get())
        self.draw_map(result.path)
        lines = [f"{algorithm} SEARCH RESULT", "=" * 70, result.message]
        if result.found:
            lines.extend([f"Book: {title}", f"Shelf: {result.target}", f"Path: {' -> '.join(result.path)}", f"Walking distance: {result.cost:g} units"])
        lines.extend(["", "OPEN LIST (remaining):", self.format_items(result.open_list), "", "CLOSED LIST (visited order):", self.format_items(result.closed_list)])
        self.write_result("\n".join(lines))

    def plan_route(self) -> None:
        self.apply_conditions()
        titles = [title for title, variable in self.book_vars.items() if variable.get()]
        limit_text = self.time_limit.get().strip()
        try:
            limit = float(limit_text) if limit_text else None
            if limit is not None and limit <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid time limit", "Enter a positive number or leave the time-limit box empty.")
            return
        route = self.model.plan_route(titles, self.start_node.get(), limit)
        self.draw_map(route.get("path", []))
        lines = ["A* MULTI-BOOK ROUTE RESULT", "=" * 70]
        if route["found"]:
            lines.extend([
                "Complete route found.",
                f"Collection order: {' -> '.join(route['order'])}",
                f"Full path: {' -> '.join(route['path'])}",
                f"Total walking distance: {route['distance']:g} units",
                f"Estimated collection time: {route['time']:g} units",
                f"Priority-adjusted route score: {route['score']:g}",
            ])
        else:
            lines.append("No complete route found.")
        lines.extend(["", "NOTES:", self.format_items(route["notes"]), "", "OPEN LIST (A* states remaining):", self.format_items(route["open_list"]), "", "CLOSED LIST (A* states expanded):", self.format_items(route["closed_list"])])
        self.write_result("\n".join(lines))

    @staticmethod
    def format_items(items: List[str]) -> str:
        return "\n".join(f"  {index}. {item}" for index, item in enumerate(items, 1)) or "  (empty)"

    def clear_conditions(self) -> None:
        for listbox in (self.closed_listbox, self.crowded_listbox, self.unavailable_listbox, self.restricted_listbox):
            listbox.selection_clear(0, "end")
        self.accessible_only.set(False)
        self.write_result("All temporary library conditions were cleared.")
        self.draw_map([])

    def write_result(self, text: str) -> None:
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", text)

    def draw_map(self, route: List[str]) -> None:
        self.canvas.delete("all")
        self.update_idletasks()
        width = max(self.canvas.winfo_width(), 700)
        height = max(self.canvas.winfo_height(), 550)
        scale_x = (width - 140) / 560
        scale_y = (height - 120) / 430

        def point(node: str) -> tuple[float, float]:
            x, y = self.model.nodes[node]
            return 70 + x * scale_x, 55 + y * scale_y

        route_edges = set(zip(route, route[1:])) | set((b, a) for a, b in zip(route, route[1:]))
        drawn = set()
        for source, edges in self.model.adjacency.items():
            for target, _ in edges:
                edge = tuple(sorted((source, target)))
                if edge in drawn:
                    continue
                drawn.add(edge)
                x1, y1 = point(source)
                x2, y2 = point(target)
                color = "#e45757" if (source, target) in route_edges else "#b8c5d1"
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=4 if color == "#e45757" else 2)
        for node, (x, y) in self.model.nodes.items():
            px, py = point(node)
            radius = 17 if node in self.model.sections or node == "Entrance" else 13
            blocked = self.model.is_blocked(node)
            fill = "#f4a261" if node == "Entrance" else ("#9da7b1" if blocked else ("#e45757" if node in route else "#4c9f70"))
            self.canvas.create_oval(px - radius, py - radius, px + radius, py + radius, fill=fill, outline="#17324d", width=2)
            self.canvas.create_text(px, py + radius + 12, text=node, fill="#17324d", font=("Segoe UI", 8, "bold" if radius > 15 else "normal"))
        self.canvas.create_text(18, 18, anchor="w", text="Red = selected route   Grey = blocked   Green = available", fill="#52677a", font=("Segoe UI", 10))


if __name__ == "__main__":
    LibraryApp().mainloop()

