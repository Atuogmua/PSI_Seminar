# BookCompare — Book Price Comparison Tool

BookCompare is a desktop application that compares book prices across ten Moldovan online bookshops — Librarius, Carturesti, Biblion, CarteaMea, BookZone, Litera, BookStore, Cartier, Cartego, and Dorinta. It lets readers, students, and book collectors find the cheapest available copy by searching by ISBN or title/author, running all ten scrapers in parallel, and presenting a grouped comparison table directly in the app that highlights the best deal.

## Features

- Search by ISBN or title / author
- Scrapes 10 bookshops in parallel using `concurrent.futures.ThreadPoolExecutor`
- Desktop GUI (Tkinter) with a styled search interface and in-app comparison table
- Results grouped by book with one column per shop — cheapest price highlighted in green
- Stores full search history in a local SQLite database (`bookcompare.db`)
- Graceful error handling — returns partial results if some shops are unreachable
- Automatic retry with exponential backoff on failed requests
- Polite scraping with randomized delays between requests

## Screenshots

![GUI window with search interface](screenshots/gui_window.png)

![Comparison table with results](screenshots/results_table.png)

## Requirements

- **Python 3.10** or higher
- **requests** — HTTP client for fetching bookshop pages
- **beautifulsoup4** — HTML parser for extracting product data from pages
- **lxml** — Fast XML/HTML parser backend used by BeautifulSoup
- **Jinja2** — Template engine for the HTML results export
- **pytest** — Test framework
- **pytest-cov** — Coverage reporting plugin for pytest
- **responses** — HTTP request mocking library for testing scrapers

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd PSI_Seminar

# 2. Create a virtual environment
python -m venv venv

# 3. Activate it
# Linux / macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Install the project in editable mode (needed for imports and tests)
pip install -e .
```

## Usage

```bash
python -m book_comparator.main
```

1. Enter a search term in the text field (e.g. a book title, author name, or ISBN).
2. Select the search type: **ISBN** or **Title / Author**.
3. Click **Search** — the app queries all 10 bookshops in parallel. The status label shows progress.
4. Results appear in-app as a comparison table with one column per shop, sorted by price with the cheapest option highlighted in green.

## Project Structure

```
book_comparator/
├── main.py                  # Entry point — configures logging, launches the GUI
├── gui/
│   └── app.py               # Desktop GUI window (Tkinter)
├── scrapers/
│   ├── base.py              # Abstract base scraper with retry logic and normalization
│   ├── librarius.py         # Scraper for librarius.md
│   ├── carturesti.py        # Scraper for carturesti.md
│   ├── biblion.py           # Scraper for biblion.md
│   ├── carteamea.py         # Scraper for carteamea.md
│   ├── bookzone.py          # Scraper for bookzone.md
│   ├── litera.py            # Scraper for litera.md
│   ├── bookstoremd.py       # Scraper for bookstore.md
│   ├── cartier.py           # Scraper for cartier.md
│   ├── cartego.py           # Scraper for cartego.md
│   └── dorinta.py           # Scraper for dorinta.md
├── models/
│   └── book.py              # Dataclasses: BookResult, SearchSession
├── services/
│   ├── search.py            # Orchestrator — runs all scrapers concurrently
│   ├── results_server.py    # Renders HTML comparison table for browser export
│   └── database.py          # SQLite persistence layer
├── templates/
│   └── results.html         # Jinja2 HTML template for the comparison table
tests/
├── conftest.py              # Shared pytest fixtures
├── test_models.py           # Tests for BookResult and SearchSession
├── test_database.py         # Tests for the SQLite database layer
├── test_scrapers.py         # Tests for each scraper (mocked HTTP)
└── test_search.py           # Tests for the search orchestrator
requirements.txt             # Pinned dependency versions
pyproject.toml               # Build config and pytest settings
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=book_comparator --cov-report=term-missing
```

## Supported Bookshops

| Shop | URL | Notes |
| --- | --- | --- |
| Librarius | https://librarius.md | Largest online bookshop in Moldova |
| Carturesti | https://carturesti.md | Romanian chain with a Moldovan branch |
| Biblion | https://biblion.md | General bookshop (WooCommerce / Savoy theme) |
| CarteaMea | https://carteamea.md | Moldovan online bookshop with pagination support |
| BookZone | https://bookzone.md | Moldovan bookshop focused on new releases |
| Litera | https://litera.md | OpenCart-based bookshop |
| BookStore | https://bookstore.md | Bitrix-based bookshop |
| Cartier | https://cartier.md | Publisher and bookshop (WooCommerce) |
| Cartego | https://cartego.md | WooCommerce bookshop with REST API |
| Dorinta | https://dorinta.md | Custom platform bookshop |
