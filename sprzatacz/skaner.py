"""Skanowanie folderu i wybór kandydatów na duplikaty."""

import logging
import os
from collections import defaultdict
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import NamedTuple

from sprzatacz.wzorce import czy_pominac

logger = logging.getLogger(__name__)


class InfoPliku(NamedTuple):
    sciezka: Path
    rozmiar: int


def skanuj(katalog: Path) -> Iterator[InfoPliku]:
    """Zwraca po kolei wszystkie pliki z katalogu i podkatalogów."""
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
    """Pomija pliki tymczasowe i mniejsze niż min_rozmiar."""
    for plik in pliki:
        if czy_pominac(plik.sciezka.name):
            logger.debug("Pomijam plik tymczasowy: %s", plik.sciezka)
            continue
        if plik.rozmiar < min_rozmiar:
            continue
        yield plik


def grupuj_po_rozmiarze(pliki: Iterable[InfoPliku]) -> dict[int, list[Path]]:
    """Grupuje pliki po rozmiarze, zostawia tylko grupy z co najmniej 2 plikami."""
    grupy: dict[int, list[Path]] = defaultdict(list)
    for plik in pliki:
        grupy[plik.rozmiar].append(plik.sciezka)
    return {rozmiar: sciezki for rozmiar, sciezki in grupy.items() if len(sciezki) > 1}
