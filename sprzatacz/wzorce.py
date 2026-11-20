"""Wyrażenia regularne do nazw plików."""

import re
from dataclasses import dataclass

PLIK_POMIJANY_RE = re.compile(
    r"^(~\$.*|.*\.(tmp|bak|swp)|thumbs\.db|desktop\.ini)$",
    re.IGNORECASE,
)

# np. "raport (2).pdf", "raport - Kopia.pdf", "raport - Copy (3).pdf"
KOPIA_RE = re.compile(
    r"^(?P<baza>.+?)"
    r"(?P<dopisek>\s-\s(?:kopia|copy))?"
    r"(?:\s\((?P<numer>\d+)\))?"
    r"(?P<rozszerzenie>\.[^.\s]+)?$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class InfoKopii:
    baza: str
    numer: int | None
    rozszerzenie: str


def czy_pominac(nazwa_pliku: str) -> bool:
    """Czy plik jest tymczasowy lub systemowy."""
    return PLIK_POMIJANY_RE.match(nazwa_pliku) is not None


def rozpoznaj_kopie(nazwa_pliku: str) -> InfoKopii | None:
    """Zwraca dane z nazwy kopii pliku albo None dla zwykłej nazwy."""
    dopasowanie = KOPIA_RE.match(nazwa_pliku)
    if dopasowanie is None:
        return None

    numer = dopasowanie.group("numer")
    if numer is None and dopasowanie.group("dopisek") is None:
        return None

    return InfoKopii(
        baza=dopasowanie.group("baza"),
        numer=int(numer) if numer else None,
        rozszerzenie=dopasowanie.group("rozszerzenie") or "",
    )
