"""Desktop GUI window for the book price comparator using Tkinter."""

import re
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from book_comparator.models.book import BookResult, SearchSession
from book_comparator.scrapers import ALL_SCRAPERS
from book_comparator.services.search import search_all

TOTAL_SHOPS = len(ALL_SCRAPERS)

SHOP_NAMES = [
    "Librarius", "Carturesti", "Biblion", "CarteaMea", "Bookzone",
    "Litera", "BookStore", "Cartier", "Cartego", "Dorinta",
]

BG = "#f0f2f5"
HEADER_BG = "#1a1a2e"
HEADER_FG = "#e0e0e0"
ACCENT = "#4361ee"
ACCENT_HOVER = "#3a56d4"
ACCENT_FG = "#ffffff"
ENTRY_BG = "#ffffff"
ENTRY_BORDER = "#c5cad3"
STATUS_FG = "#6b7280"
TABLE_HEAD_BG = "#2d3142"
TABLE_HEAD_FG = "#ffffff"
TABLE_ROW_EVEN = "#ffffff"
TABLE_ROW_ODD = "#f8f9fb"
TABLE_SELECT = "#dbeafe"
BEST_BG = "#d1fae5"
BEST_FG = "#065f46"
FONT = "Segoe UI"


def _group_results(results: list[BookResult]) -> list[dict]:
    groups: dict[str, dict] = {}
    order: list[str] = []

    for book in results:
        if book.isbn:
            key = f"isbn:{book.isbn.strip()}"
        else:
            key = f"title:{re.sub(r'\\s+', ' ', book.title.strip().lower())}"

        if key not in groups:
            groups[key] = {
                "title": book.title,
                "author": book.author,
                "isbn": book.isbn,
                "shops": {},
                "best_price": None,
            }
            order.append(key)

        g = groups[key]
        if book.author and not g["author"]:
            g["author"] = book.author
        if book.isbn and not g["isbn"]:
            g["isbn"] = book.isbn

        g["shops"][book.shop_name] = book.price

        if book.price is not None:
            if g["best_price"] is None or book.price < g["best_price"]:
                g["best_price"] = book.price

    grouped = [groups[k] for k in order]
    grouped.sort(key=lambda g: (g["best_price"] is None, g["best_price"] or 0))
    return grouped


class BookComparatorApp:
    """Main application window for book price comparison."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("BookCompare")
        self.root.geometry("1200x650")
        self.root.minsize(800, 450)
        self.root.configure(bg=BG)
        self._center_window()

        self._session: SearchSession | None = None
        self._results: list[BookResult] = []
        self._apply_theme()
        self._build_ui()

    def _center_window(self) -> None:
        self.root.update_idletasks()
        w, h = 1200, 650
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _apply_theme(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Treeview",
                        font=(FONT, 10),
                        rowheight=30,
                        background=TABLE_ROW_EVEN,
                        fieldbackground=TABLE_ROW_EVEN,
                        foreground="#1f2937",
                        borderwidth=0)
        style.configure("Treeview.Heading",
                        font=(FONT, 9, "bold"),
                        background=TABLE_HEAD_BG,
                        foreground=TABLE_HEAD_FG,
                        borderwidth=0,
                        padding=(8, 6))
        style.map("Treeview.Heading",
                  background=[("active", "#3d4258")])
        style.map("Treeview",
                  background=[("selected", TABLE_SELECT)],
                  foreground=[("selected", "#1f2937")])

        style.configure("Accent.TButton",
                        font=(FONT, 10, "bold"),
                        background=ACCENT,
                        foreground=ACCENT_FG,
                        borderwidth=0,
                        padding=(20, 8),
                        focuscolor="")
        style.map("Accent.TButton",
                  background=[("active", ACCENT_HOVER),
                              ("disabled", "#a0aec0")])

        style.configure("Search.TRadiobutton",
                        font=(FONT, 10),
                        background=BG,
                        foreground="#374151",
                        focuscolor="")
        style.map("Search.TRadiobutton",
                  background=[("active", BG)])

        style.configure("TScrollbar",
                        background="#d1d5db",
                        troughcolor=BG,
                        borderwidth=0,
                        arrowsize=12)

    def _build_ui(self) -> None:
        header = tk.Frame(self.root, bg=HEADER_BG, height=56)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(
            header,
            text="BookCompare",
            font=(FONT, 16, "bold"),
            bg=HEADER_BG,
            fg=HEADER_FG,
        ).pack(side=tk.LEFT, padx=24)
        tk.Label(
            header,
            text="Price Comparison Tool",
            font=(FONT, 10),
            bg=HEADER_BG,
            fg="#9ca3af",
        ).pack(side=tk.LEFT, padx=(0, 24))

        search_panel = tk.Frame(self.root, bg=BG)
        search_panel.pack(fill=tk.X, padx=24, pady=(20, 0))

        search_card = tk.Frame(search_panel, bg="#ffffff", highlightbackground=ENTRY_BORDER,
                               highlightthickness=1, padx=20, pady=16)
        search_card.pack(fill=tk.X)

        search_row = tk.Frame(search_card, bg="#ffffff")
        search_row.pack(fill=tk.X)

        self.query_var = tk.StringVar()
        self.query_entry = tk.Entry(
            search_row,
            textvariable=self.query_var,
            font=(FONT, 12),
            bg=ENTRY_BG,
            fg="#1f2937",
            insertbackground="#1f2937",
            relief=tk.SOLID,
            borderwidth=1,
            highlightthickness=2,
            highlightcolor=ACCENT,
            highlightbackground=ENTRY_BORDER,
        )
        self.query_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 12))
        self.query_entry.bind("<Return>", lambda e: self._on_search())

        self.search_btn = ttk.Button(
            search_row,
            text="Search",
            command=self._on_search,
            style="Accent.TButton",
        )
        self.search_btn.pack(side=tk.LEFT)

        bottom_row = tk.Frame(search_card, bg="#ffffff")
        bottom_row.pack(fill=tk.X, pady=(10, 0))

        self.search_type_var = tk.StringVar(value="title_author")
        for text, value in [("ISBN", "isbn"), ("Title / Author", "title_author")]:
            ttk.Radiobutton(
                bottom_row,
                text=text,
                variable=self.search_type_var,
                value=value,
                style="Search.TRadiobutton",
            ).pack(side=tk.LEFT, padx=(0, 16))

        self.status_var = tk.StringVar(value="")
        self.status_label = tk.Label(
            bottom_row,
            textvariable=self.status_var,
            font=(FONT, 10),
            bg="#ffffff",
            fg=STATUS_FG,
        )
        self.status_label.pack(side=tk.RIGHT)

        self.table_frame = tk.Frame(self.root, bg=BG)
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=(16, 24))

        self._build_tree()

    def _build_tree(self, shop_names: list[str] | None = None) -> None:
        for w in self.table_frame.winfo_children():
            w.destroy()

        if shop_names is None:
            shop_names = SHOP_NAMES

        card = tk.Frame(self.table_frame, bg="#ffffff", highlightbackground=ENTRY_BORDER,
                        highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True)

        columns = ("num", "title", "author", "isbn") + tuple(shop_names)

        self.tree = ttk.Treeview(
            card,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        self.tree.heading("num", text="#")
        self.tree.heading("title", text="Title")
        self.tree.heading("author", text="Author")
        self.tree.heading("isbn", text="ISBN")

        self.tree.column("num", width=35, minwidth=30, anchor=tk.CENTER, stretch=False)
        self.tree.column("title", width=220, minwidth=100)
        self.tree.column("author", width=140, minwidth=70)
        self.tree.column("isbn", width=115, minwidth=90)

        for shop in shop_names:
            self.tree.heading(shop, text=shop)
            self.tree.column(shop, width=85, minwidth=60, anchor=tk.CENTER)

        vsb = ttk.Scrollbar(card, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(card, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        card.rowconfigure(0, weight=1)
        card.columnconfigure(0, weight=1)

        self.tree.tag_configure("even", background=TABLE_ROW_EVEN)
        self.tree.tag_configure("odd", background=TABLE_ROW_ODD)
        self.tree.tag_configure("best", background=BEST_BG, foreground=BEST_FG)

        self._active_shops = shop_names

    def _on_search(self) -> None:
        query = self.query_var.get().strip()
        if not query:
            messagebox.showwarning("Input required", "Please enter a search term.")
            return

        search_type = self.search_type_var.get()

        self.search_btn.configure(state=tk.DISABLED)
        self.query_entry.configure(state=tk.DISABLED)
        self.tree.delete(*self.tree.get_children())
        self.status_var.set(f"Searching {TOTAL_SHOPS} bookshops...")
        self.status_label.configure(fg=ACCENT)

        def do_search() -> None:
            try:
                results, session, failed = search_all(query, search_type)
                self.root.after(0, lambda: self._on_search_complete(results, session, failed))
            except Exception as e:
                self.root.after(0, lambda: self._on_search_error(str(e)))

        threading.Thread(target=do_search, daemon=True).start()

    def _on_search_complete(
        self, results: list[BookResult], session: SearchSession, failed: int
    ) -> None:
        self._results = results
        self._session = session

        self.search_btn.configure(state=tk.NORMAL)
        self.query_entry.configure(state=tk.NORMAL)
        self.status_label.configure(fg=STATUS_FG)

        if failed >= TOTAL_SHOPS:
            messagebox.showerror(
                "Connection Error",
                "All bookshops are unreachable. Check your internet connection.",
            )
            self.status_var.set("Error: all bookshops unreachable")
            self.status_label.configure(fg="#dc2626")
            return

        if results:
            shops = len({r.shop_name for r in results})
            msg = f"Found {len(results)} results across {shops} shops"
            if failed > 0:
                msg += f" ({failed} unreachable)"
            self.status_var.set(msg)
            self._populate_table(results)
        else:
            msg = "No results found"
            if failed > 0:
                msg += f" ({failed} shops unreachable)"
            self.status_var.set(msg)

    def _populate_table(self, results: list[BookResult]) -> None:
        present_shops = [s for s in SHOP_NAMES if any(r.shop_name == s for r in results)]
        if present_shops != getattr(self, "_active_shops", None):
            self._build_tree(present_shops)

        self.tree.delete(*self.tree.get_children())
        grouped = _group_results(results)

        for idx, book in enumerate(grouped, 1):
            values = [
                idx,
                book["title"],
                book["author"] or "—",
                book["isbn"] or "—",
            ]
            has_best = False
            for shop in present_shops:
                price = book["shops"].get(shop)
                if price is not None:
                    values.append(f"{price:.2f}")
                    if price == book["best_price"]:
                        has_best = True
                else:
                    values.append("—")

            if has_best and len(book["shops"]) > 1:
                tag = "best"
            elif idx % 2 == 0:
                tag = "even"
            else:
                tag = "odd"
            self.tree.insert("", tk.END, values=values, tags=(tag,))

    def _on_search_error(self, message: str) -> None:
        self.search_btn.configure(state=tk.NORMAL)
        self.query_entry.configure(state=tk.NORMAL)
        self.status_var.set(f"Error: {message}")
        self.status_label.configure(fg="#dc2626")

    def run(self) -> None:
        self.root.mainloop()
