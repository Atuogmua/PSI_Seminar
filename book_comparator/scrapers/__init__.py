"""Bookstore scrapers package."""

from .base import BaseBookScraper
from .biblion import BiblionScraper
from .bookstoremd import BookstoreMdScraper
from .bookzone import BookzoneScraper
# from .carteamea import CarteameaScraper
from .cartego import CartegoScraper
from .cartier import CartierScraper
from .carturesti import CarturestiScraper
from .dorinta import DorintaScraper
# from .elefant import ElefantScraper
from .librarius import LibrariusScraper
from .litera import LiteraScraper
# from .mesageria import MesageriaScraper

ALL_SCRAPERS = [
    LibrariusScraper,
    CarturestiScraper,
    BiblionScraper,
    # CarteameaScraper,
    BookzoneScraper,
    LiteraScraper,
    BookstoreMdScraper,
    CartierScraper,
    CartegoScraper,
    DorintaScraper,
    # ElefantScraper,
    # MesageriaScraper,
]

__all__ = [
    "BaseBookScraper",
    "LibrariusScraper",
    "CarturestiScraper",
    "BiblionScraper",
    # "CarteameaScraper",
    "BookzoneScraper",
    "LiteraScraper",
    "BookstoreMdScraper",
    "CartierScraper",
    "CartegoScraper",
    "DorintaScraper",
    # "ElefantScraper",
    # "MesageriaScraper",
    "ALL_SCRAPERS",
]
