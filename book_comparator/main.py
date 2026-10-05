"""Entry point — launches the book price comparator GUI."""

from book_comparator.gui.app import BookComparatorApp


def main() -> None:
    """Create and run the application."""
    app = BookComparatorApp()
    app.run()


if __name__ == "__main__":
    main()
