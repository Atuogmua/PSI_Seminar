"""Desktop GUI window for the book price comparator using Tkinter."""

import threading
import tkinter as tk
from tkinter import ttk, messagebox

from book_comparator.services.search import search_all
from book_comparator.services.results_server import serve_results


class BookComparatorApp:
    """Main application window for book price comparison."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Comparator Prețuri Cărți")
        self.root.geometry("900x600")
        self.root.minsize(700, 450)
        self.root.configure(bg="#f0f2f5")

        self._server = None
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the application UI components."""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), background="#f0f2f5", foreground="#2c3e50")
        style.configure("TFrame", background="#f0f2f5")
        style.configure("TLabel", background="#f0f2f5", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=28)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=20, pady=(20, 10))
        ttk.Label(header, text="Comparator Prețuri Cărți", style="Title.TLabel").pack()

        search_frame = ttk.Frame(self.root)
        search_frame.pack(fill=tk.X, padx=20, pady=5)

        ttk.Label(search_frame, text="Caută:").grid(row=0, column=0, padx=(0, 8), sticky=tk.W)
        self.query_var = tk.StringVar()
        self.query_entry = ttk.Entry(search_frame, textvariable=self.query_var, width=50, font=("Segoe UI", 11))
        self.query_entry.grid(row=0, column=1, padx=(0, 12), sticky=tk.EW)
        self.query_entry.bind("<Return>", lambda e: self._on_search())

        ttk.Label(search_frame, text="Tip:").grid(row=0, column=2, padx=(0, 8), sticky=tk.W)
        self.search_type_var = tk.StringVar(value="title")
        type_combo = ttk.Combobox(
            search_frame,
            textvariable=self.search_type_var,
            values=["title", "author", "isbn"],
            state="readonly",
            width=10,
        )
        type_combo.grid(row=0, column=3, padx=(0, 12))

        self.search_btn = ttk.Button(search_frame, text="Caută", command=self._on_search)
        self.search_btn.grid(row=0, column=4, padx=(0, 4))

        self.browser_btn = ttk.Button(search_frame, text="Deschide în browser", command=self._open_in_browser, state=tk.DISABLED)
        self.browser_btn.grid(row=0, column=5)

        search_frame.columnconfigure(1, weight=1)

        self.status_var = tk.StringVar(value="Introduceți un termen de căutare.")
        status_label = ttk.Label(self.root, textvariable=self.status_var, foreground="#7f8c8d")
        status_label.pack(fill=tk.X, padx=20, pady=(4, 8))

        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        columns = ("nr", "title", "author", "price", "shop", "url")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("nr", text="#")
        self.tree.heading("title", text="Titlu")
        self.tree.heading("author", text="Autor")
        self.tree.heading("price", text="Preț")
        self.tree.heading("shop", text="Magazin")
        self.tree.heading("url", text="URL")

        self.tree.column("nr", width=40, stretch=False, anchor=tk.CENTER)
        self.tree.column("title", width=280)
        self.tree.column("author", width=180)
        self.tree.column("price", width=100, anchor=tk.E)
        self.tree.column("shop", width=100, anchor=tk.CENTER)
        self.tree.column("url", width=160)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._results = []

    def _on_search(self) -> None:
        """Handle search button click — runs scrapers in a background thread."""
        query = self.query_var.get().strip()
        if not query:
            messagebox.showwarning("Atenție", "Introduceți un termen de căutare.")
            return

        search_type = self.search_type_var.get()
        self.search_btn.configure(state=tk.DISABLED)
        self.browser_btn.configure(state=tk.DISABLED)
        self.status_var.set(f"Se caută '{query}' ({search_type})...")

        for item in self.tree.get_children():
            self.tree.delete(item)

        def do_search() -> None:
            results = search_all(query, search_type)
            self.root.after(0, lambda: self._display_results(results, query, search_type))

        threading.Thread(target=do_search, daemon=True).start()

    def _display_results(self, results: list, query: str, search_type: str) -> None:
        """Update the treeview with search results (called on main thread)."""
        self._results = results
        self._last_query = query
        self._last_search_type = search_type

        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, book in enumerate(results, 1):
            self.tree.insert("", tk.END, values=(
                i,
                book.title,
                book.author or "—",
                f"{book.price:.2f} {book.currency}",
                book.shop_name,
                book.source_url,
            ))

        self.search_btn.configure(state=tk.NORMAL)
        if results:
            self.browser_btn.configure(state=tk.NORMAL)
            self.status_var.set(f"{len(results)} rezultat(e) găsite pentru '{query}'.")
        else:
            self.status_var.set(f"Nu s-au găsit rezultate pentru '{query}'.")

    def _open_in_browser(self) -> None:
        """Serve results as HTML and open in the default browser."""
        if not self._results:
            return

        if self._server:
            self._server.shutdown()

        self._server = serve_results(
            self._results,
            self._last_query,
            self._last_search_type,
        )
        self.status_var.set("Rezultatele au fost deschise în browser (http://127.0.0.1:8080).")

    def run(self) -> None:
        """Start the Tkinter main loop."""
        self.root.mainloop()

        if self._server:
            self._server.shutdown()
