"""Bookstore scrapers package."""

from .biblion import BiblionScraper
from .bookzone import BookzoneScraper
from .carteamea import CarteameaScraper
from .carturesti import CarturestiScraper
from .librarius import LibrariusScraper

ALL_SCRAPERS = [
    LibrariusScraper,
    CarturestiScraper,
    BiblionScraper,
    CarteameaScraper,
    BookzoneScraper,
]

__all__ = [
    "LibrariusScraper",
    "CarturestiScraper",
    "BiblionScraper",
    "CarteameaScraper",
    "BookzoneScraper",
    "ALL_SCRAPERS",
]
