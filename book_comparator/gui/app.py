"""Desktop GUI window for the book price comparator using Tkinter."""

import threading
import tkinter as tk
from tkinter import messagebox

from book_comparator.models.book import SearchSession
from book_comparator.scrapers import ALL_SCRAPERS
from book_comparator.services.search import search_all
from book_comparator.services.results_server import serve_results

TOTAL_SHOPS = len(ALL_SCRAPERS)


class BookComparatorApp:
    """Main application window for book price comparison.

    Window: 500x350, centered, non-resizable.
    """

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("BookCompare — Price Comparison Tool")
        self.root.geometry("500x350")
        self.root.resizable(False, False)
        self._center_window()

        self._session: SearchSession | None = None
        self._results: list = []
        self._build_ui()

    def _center_window(self) -> None:
        """Center the window on screen."""
        self.root.update_idletasks()
        w, h = 500, 350
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self) -> None:
        """Build the application UI components."""
        pad_x = 30
        tk.Label(self.root, text="Search for a book", font=("Segoe UI", 14, "bold")).pack(
            pady=(24, 8),
        )

        self.query_var = tk.StringVar()
        self.query_entry = tk.Entry(
            self.root,
            textvariable=self.query_var,
            width=40,
            font=("Segoe UI", 11),
        )
        self.query_entry.pack(padx=pad_x, pady=(0, 12))
        self.query_entry.bind("<Return>", lambda e: self._on_search())

        radio_frame = tk.Frame(self.root)
        radio_frame.pack(pady=(0, 12))

        self.search_type_var = tk.StringVar(value="title")
        for text, value in [("ISBN", "isbn"), ("Title", "title"), ("Author", "author")]:
            tk.Radiobutton(
                radio_frame,
                text=text,
                variable=self.search_type_var,
                value=value,
                font=("Segoe UI", 10),
            ).pack(side=tk.LEFT, padx=10)

        self.search_btn = tk.Button(
            self.root,
            text="Search",
            command=self._on_search,
            font=("Segoe UI", 10, "bold"),
            width=15,
        )
        self.search_btn.pack(pady=(0, 12))

        self.status_var = tk.StringVar(value="")
        self.status_label = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("Segoe UI", 10),
            fg="#555",
            wraplength=440,
        )
        self.status_label.pack(padx=pad_x, pady=(0, 12))

        self.view_btn = tk.Button(
            self.root,
            text="View Results",
            command=self._on_view_results,
            font=("Segoe UI", 10),
            width=15,
            state=tk.DISABLED,
        )
        self.view_btn.pack(pady=(0, 16))

    def _on_search(self) -> None:
        """Handle Search button click — runs scrapers in a background thread."""
        query = self.query_var.get().strip()
        if not query:
            messagebox.showwarning("Input required", "Please enter a search term.")
            return

        search_type = self.search_type_var.get()

        self.search_btn.configure(state=tk.DISABLED)
        self.query_entry.configure(state=tk.DISABLED)
        self.view_btn.configure(state=tk.DISABLED)
        self.status_var.set(f"Searching {TOTAL_SHOPS} bookshops...")

        def do_search() -> None:
            """Run search in background thread."""
            try:
                results, session, failed = search_all(query, search_type)
                self.root.after(0, lambda: self._on_search_complete(results, session, failed))
            except Exception as e:
                self.root.after(0, lambda: self._on_search_error(str(e)))

        threading.Thread(target=do_search, daemon=True).start()

    def _on_search_complete(
        self, results: list, session: SearchSession, failed: int
    ) -> None:
        """Handle search completion on the main thread."""
        self._results = results
        self._session = session

        self.search_btn.configure(state=tk.NORMAL)
        self.query_entry.configure(state=tk.NORMAL)

        if failed >= TOTAL_SHOPS:
            messagebox.showerror(
                "Connection Error",
                "All bookshops are unreachable. Check your internet connection.",
            )
            self.status_var.set("Error: all bookshops unreachable")
            self.view_btn.configure(state=tk.DISABLED)
            return

        if results:
            shops = len({r.shop_name for r in results})
            msg = f"Found {len(results)} results across {shops} shops"
            if failed > 0:
                msg += f" ({failed} shops unreachable)"
            self.status_var.set(msg)
            self.view_btn.configure(state=tk.NORMAL)
        else:
            msg = "No results found"
            if failed > 0:
                msg += f" ({failed} shops unreachable)"
            self.status_var.set(msg)
            self.view_btn.configure(state=tk.DISABLED)

    def _on_search_error(self, message: str) -> None:
        """Handle search error on the main thread."""
        self.search_btn.configure(state=tk.NORMAL)
        self.query_entry.configure(state=tk.NORMAL)
        self.status_var.set(f"Error: {message}")

    def _on_view_results(self) -> None:
        """Open the HTML results page in the default browser."""
        if not self._session:
            return
        serve_results(self._session)

    def run(self) -> None:
        """Start the Tkinter main loop."""
        self.root.mainloop()
