"""Wyrażenia regularne używane w projekcie.

Dwa wzorce:
  * PLIK_POMIJANY_RE – rozpoznaje pliki tymczasowe/systemowe, których nie warto
    sprawdzać (walidacja nazwy pliku),
  * KOPIA_RE – wyciąga z nazwy pliku informację, że jest to kopia, np.
    "raport (2).pdf" albo "zdjecie - Kopia.jpg" (ekstrakcja danych, grupy nazwane).
"""

import re
from dataclasses import dataclass

# Pliki, które pomijamy: tymczasowe pliki Office (~$...), *.tmp, *.bak, *.swp
# oraz pliki systemowe Windows. re.IGNORECASE -> wielkość liter nie ma znaczenia.
PLIK_POMIJANY_RE = re.compile(
    r"^(~\$.*|.*\.(tmp|bak|swp)|thumbs\.db|desktop\.ini)$",
    re.IGNORECASE,
)

# Nazwa kopii pliku. Grupy nazwane:
#   baza         – nazwa bez dopisku o kopii, np. "raport"
#   dopisek      – " - Kopia" lub " - Copy" (może go nie być)
#   numer        – numer kopii z nawiasu, np. "2" (może go nie być)
#   rozszerzenie – np. ".pdf" (może go nie być)
# Pasuje do: "raport (2).pdf", "raport - Kopia.pdf", "raport - Copy (3).pdf"
KOPIA_RE = re.compile(
    r"^(?P<baza>.+?)"                         # nazwa bazowa (leniwie, jak najkrócej)
    r"(?P<dopisek>\s-\s(?:kopia|copy))?"      # opcjonalnie " - Kopia" / " - Copy"
    r"(?:\s\((?P<numer>\d+)\))?"              # opcjonalnie " (2)"
    r"(?P<rozszerzenie>\.[^.\s]+)?$",         # opcjonalnie rozszerzenie
    re.IGNORECASE,
)


@dataclass(frozen=True)
class InfoKopii:
    """Informacje wyciągnięte z nazwy pliku-kopii."""

    baza: str
    numer: int | None
    rozszerzenie: str


def czy_pominac(nazwa_pliku: str) -> bool:
    """Zwraca True, jeśli plik jest tymczasowy/systemowy i należy go pominąć."""
    return PLIK_POMIJANY_RE.match(nazwa_pliku) is not None


def rozpoznaj_kopie(nazwa_pliku: str) -> InfoKopii | None:
    """Sprawdza, czy nazwa wygląda na kopię pliku.

    Zwraca InfoKopii dla nazw typu "raport (2).pdf" lub "raport - Kopia.pdf",
    a None dla zwykłych nazw (np. "raport.pdf").
    """
    dopasowanie = KOPIA_RE.match(nazwa_pliku)
    if dopasowanie is None:
        return None

    numer = dopasowanie.group("numer")
    if numer is None and dopasowanie.group("dopisek") is None:
        return None  # zwykła nazwa, bez oznaczenia kopii

    return InfoKopii(
        baza=dopasowanie.group("baza"),
        numer=int(numer) if numer else None,
        rozszerzenie=dopasowanie.group("rozszerzenie") or "",
    )
