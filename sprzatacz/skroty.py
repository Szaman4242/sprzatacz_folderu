"""Liczenie skrótów SHA-256: sekwencyjnie, wątkami albo procesami."""

import hashlib
import logging
import threading
from collections import defaultdict
from collections.abc import Iterable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path

from sprzatacz.czytnik import CzytnikPliku
from sprzatacz.dekoratory import ponow, zmierz_czas

logger = logging.getLogger(__name__)

TRYBY = ("sekwencyjnie", "watki", "procesy")


# FileNotFoundError nie ma sensu ponawiać, PermissionError tak (plik zablokowany)
@ponow(proby=3, opoznienie=0.2, wyjatki=(PermissionError,))
def oblicz_skrot(sciezka: Path) -> str:
    """Skrót SHA-256 pliku jako tekst szesnastkowy."""
    skrot = hashlib.sha256()
    with CzytnikPliku(sciezka) as czytnik:
        for kawalek in czytnik:
            skrot.update(kawalek)
    return skrot.hexdigest()


def skrot_pliku(sciezka: Path) -> tuple[Path, str | None]:
    """Zwraca (ścieżka, skrót), a przy błędzie odczytu (ścieżka, None)."""
    try:
        return sciezka, oblicz_skrot(sciezka)
    except OSError as blad:
        logger.warning("Nie mogę odczytać %s: %s", sciezka, blad)
        return sciezka, None


class ZbieraczWynikow:
    """Wyniki zapisywane przez wiele wątków, chronione blokadą."""

    def __init__(self) -> None:
        self._blokada = threading.Lock()
        self.po_skrocie: dict[str, list[Path]] = defaultdict(list)
        self.przetworzone = 0

    def dodaj(self, sciezka: Path, skrot: str | None) -> None:
        with self._blokada:
            if skrot is not None:
                self.po_skrocie[skrot].append(sciezka)
            self.przetworzone += 1

    def duplikaty(self) -> list[list[Path]]:
        return [grupa for grupa in self.po_skrocie.values() if len(grupa) > 1]


def _licz_sekwencyjnie(kandydaci: Iterable[Path], zbieracz: ZbieraczWynikow) -> None:
    for sciezka in kandydaci:
        zbieracz.dodaj(*skrot_pliku(sciezka))


def _licz_watkami(
    kandydaci: Iterable[Path], zbieracz: ZbieraczWynikow, pracownicy: int | None
) -> None:
    def zadanie(sciezka: Path) -> None:
        zbieracz.dodaj(*skrot_pliku(sciezka))

    with ThreadPoolExecutor(max_workers=pracownicy) as pula:
        list(pula.map(zadanie, kandydaci))


def _licz_procesami(
    kandydaci: Iterable[Path], zbieracz: ZbieraczWynikow, pracownicy: int | None
) -> None:
    # procesy nie widzą zbieracza, więc wyniki zapisuje proces główny
    with ProcessPoolExecutor(max_workers=pracownicy) as pula:
        for sciezka, skrot in pula.map(skrot_pliku, kandydaci, chunksize=4):
            zbieracz.dodaj(sciezka, skrot)


@zmierz_czas
def znajdz_duplikaty(
    grupy: dict[int, list[Path]],
    tryb: str = "watki",
    pracownicy: int | None = None,
) -> list[list[Path]]:
    """Zwraca grupy plików o identycznej treści."""
    if tryb not in TRYBY:
        raise ValueError(f"Nieznany tryb '{tryb}', dostępne: {', '.join(TRYBY)}")
    if pracownicy is not None and pracownicy < 1:
        raise ValueError("Liczba pracowników musi być co najmniej 1")

    kandydaci = [sciezka for sciezki in grupy.values() for sciezka in sciezki]
    zbieracz = ZbieraczWynikow()

    if tryb == "sekwencyjnie":
        _licz_sekwencyjnie(kandydaci, zbieracz)
    elif tryb == "watki":
        _licz_watkami(kandydaci, zbieracz, pracownicy)
    else:
        _licz_procesami(kandydaci, zbieracz, pracownicy)

    logger.debug("Przetworzono %d z %d plików", zbieracz.przetworzone, len(kandydaci))
    return zbieracz.duplikaty()
