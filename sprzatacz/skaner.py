"""Skanowanie folderu – potok generatorów.

Przepływ danych (każdy krok to generator, pliki "płyną" po jednym):

    skanuj(katalog)  ->  filtruj(pliki)  ->  grupuj_po_rozmiarze(pliki)
    (wszystkie pliki)    (bez tymczasowych    (słownik: rozmiar -> lista plików,
                          i za małych)         tylko grupy z >= 2 plikami)

Dzięki generatorom nie trzymamy w pamięci listy wszystkich plików naraz.
"""

import logging
import os
from collections import defaultdict
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import NamedTuple

from sprzatacz.wzorce import czy_pominac

logger = logging.getLogger(__name__)


class InfoPliku(NamedTuple):
    """Ścieżka do pliku i jego rozmiar w bajtach."""

    sciezka: Path
    rozmiar: int


def skanuj(katalog: Path) -> Iterator[InfoPliku]:
    """Rekurencyjnie zwraca wszystkie pliki z katalogu i jego podkatalogów.

    Funkcja-generator: zamiast budować listę, oddaje pliki po jednym (yield).
    Dla podkatalogów wywołuje samą siebie i przekazuje dalej ich wyniki
    za pomocą ``yield from``.
    """
    try:
        wpisy = os.scandir(katalog)
    except (PermissionError, FileNotFoundError) as blad:
        logger.warning("Pomijam katalog %s: %s", katalog, blad)
        return

    with wpisy:
        for wpis in wpisy:
            try:
                if wpis.is_dir(follow_symlinks=False):
                    yield from skanuj(Path(wpis.path))
                elif wpis.is_file(follow_symlinks=False):
                    yield InfoPliku(Path(wpis.path), wpis.stat().st_size)
            except OSError as blad:
                logger.warning("Nie mogę odczytać %s: %s", wpis.path, blad)


def filtruj(pliki: Iterable[InfoPliku], min_rozmiar: int = 1) -> Iterator[InfoPliku]:
    """Przepuszcza dalej tylko pliki, które warto sprawdzać.

    Odrzuca pliki tymczasowe/systemowe (regex z modułu wzorce) oraz pliki
    mniejsze niż ``min_rozmiar`` bajtów (np. puste).
    """
    for plik in pliki:
        if czy_pominac(plik.sciezka.name):
            logger.debug("Pomijam plik tymczasowy: %s", plik.sciezka)
            continue
        if plik.rozmiar < min_rozmiar:
            continue
        yield plik


def grupuj_po_rozmiarze(pliki: Iterable[InfoPliku]) -> dict[int, list[Path]]:
    """Grupuje pliki według rozmiaru i zostawia tylko grupy z co najmniej 2 plikami.

    Pliki o różnym rozmiarze na pewno nie są duplikatami, więc dalej
    (liczenie skrótów SHA-256) sprawdzamy tylko te o identycznym rozmiarze.
    """
    grupy: dict[int, list[Path]] = defaultdict(list)
    for plik in pliki:
        grupy[plik.rozmiar].append(plik.sciezka)
    return {rozmiar: sciezki for rozmiar, sciezki in grupy.items() if len(sciezki) > 1}
