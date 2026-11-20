"""Liczenie skrótów SHA-256 i wyszukiwanie prawdziwych duplikatów.

Dwa pliki są duplikatami, jeśli mają identyczny skrót SHA-256. Liczymy go
tylko dla plików o tym samym rozmiarze (kandydatów ze skaner.py).
"""

import hashlib
import logging
from collections import defaultdict
from pathlib import Path

from sprzatacz.czytnik import CzytnikPliku

logger = logging.getLogger(__name__)


def oblicz_skrot(sciezka: Path) -> str:
    """Zwraca skrót SHA-256 pliku jako tekst szesnastkowy (64 znaki).

    Plik jest czytany kawałkami przez iterator CzytnikPliku, więc nawet
    bardzo duży plik nie trafia w całości do pamięci.
    """
    skrot = hashlib.sha256()
    with CzytnikPliku(sciezka) as czytnik:
        for kawalek in czytnik:
            skrot.update(kawalek)
    return skrot.hexdigest()


def znajdz_duplikaty(grupy: dict[int, list[Path]]) -> list[list[Path]]:
    """Zwraca listę grup duplikatów (każda grupa to pliki o identycznej treści).

    ``grupy`` to wynik grupuj_po_rozmiarze(): rozmiar -> lista plików.
    Wersja sekwencyjna – pliki są przetwarzane jeden po drugim.
    """
    duplikaty: list[list[Path]] = []
    for sciezki in grupy.values():
        po_skrocie: dict[str, list[Path]] = defaultdict(list)
        for sciezka in sciezki:
            try:
                po_skrocie[oblicz_skrot(sciezka)].append(sciezka)
            except OSError as blad:
                logger.warning("Nie mogę odczytać %s: %s", sciezka, blad)
        duplikaty.extend(grupa for grupa in po_skrocie.values() if len(grupa) > 1)
    return duplikaty
