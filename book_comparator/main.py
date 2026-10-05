"""Entry point — launches the book price comparator GUI."""

import logging

from book_comparator.gui.app import BookComparatorApp


def _configure_logging() -> None:
    """Configure logging: DEBUG to bookcompare.log, INFO to console."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler("bookcompare.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s"
    ))

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def main() -> None:
    """Create and run the application."""
    _configure_logging()
    app = BookComparatorApp()
    app.run()


if __name__ == "__main__":
    main()
