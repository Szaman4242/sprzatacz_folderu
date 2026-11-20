"""Liczenie skrótów SHA-256 i wyszukiwanie prawdziwych duplikatów.

Dwa pliki są duplikatami, jeśli mają identyczny skrót SHA-256. Liczymy go
tylko dla plików o tym samym rozmiarze (kandydatów ze skaner.py).

Trzy tryby pracy:
  * sekwencyjnie – pliki jeden po drugim,
  * watki        – ThreadPoolExecutor; wątki same zapisują wyniki do wspólnego
                   obiektu, więc zapis jest chroniony blokadą (Lock),
  * procesy      – ProcessPoolExecutor; procesy mają osobną pamięć, więc
                   zwracają wyniki, a zapisuje je proces główny.
"""

import hashlib
import logging
import threading
from collections import defaultdict
from collections.abc import Iterable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path

from sprzatacz.czytnik import CzytnikPliku

logger = logging.getLogger(__name__)

TRYBY = ("sekwencyjnie", "watki", "procesy")


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


def skrot_pliku(sciezka: Path) -> tuple[Path, str | None]:
    """Zwraca parę (ścieżka, skrót). Gdy pliku nie da się odczytać, skrót to None.

    Funkcja jest zdefiniowana na poziomie modułu, bo ProcessPoolExecutor musi
    móc ją przesłać do innego procesu (pickle).
    """
    try:
        return sciezka, oblicz_skrot(sciezka)
    except OSError as blad:
        logger.warning("Nie mogę odczytać %s: %s", sciezka, blad)
        return sciezka, None


class ZbieraczWynikow:
    """Wspólne miejsce na wyniki, do którego może pisać wiele wątków naraz.

    Każdy zapis odbywa się pod blokadą (threading.Lock). Bez niej dwa wątki
    mogłyby jednocześnie zmieniać słownik i licznik, a wtedy np. operacja
    ``przetworzone += 1`` mogłaby zgubić jedno zwiększenie.
    """

    def __init__(self) -> None:
        self._blokada = threading.Lock()
        self.po_skrocie: dict[str, list[Path]] = defaultdict(list)
        self.przetworzone = 0

    def dodaj(self, sciezka: Path, skrot: str | None) -> None:
        """Zapisuje wynik dla jednego pliku (bezpiecznie dla wątków)."""
        with self._blokada:
            if skrot is not None:
                self.po_skrocie[skrot].append(sciezka)
            self.przetworzone += 1

    def duplikaty(self) -> list[list[Path]]:
        """Zwraca grupy plików o identycznym skrócie (co najmniej 2 pliki)."""
        return [grupa for grupa in self.po_skrocie.values() if len(grupa) > 1]


def _licz_sekwencyjnie(kandydaci: Iterable[Path], zbieracz: ZbieraczWynikow) -> None:
    for sciezka in kandydaci:
        zbieracz.dodaj(*skrot_pliku(sciezka))


def _licz_watkami(
    kandydaci: Iterable[Path], zbieracz: ZbieraczWynikow, pracownicy: int | None
) -> None:
    def zadanie(sciezka: Path) -> None:
        # Każdy wątek sam zapisuje swój wynik do wspólnego zbieracza (pod Lockiem).
        zbieracz.dodaj(*skrot_pliku(sciezka))

    with ThreadPoolExecutor(max_workers=pracownicy) as pula:
        list(pula.map(zadanie, kandydaci))  # list() czeka na wszystkie wątki


def _licz_procesami(
    kandydaci: Iterable[Path], zbieracz: ZbieraczWynikow, pracownicy: int | None
) -> None:
    # Procesy nie widzą obiektu zbieracz (osobna pamięć), więc tylko zwracają
    # wyniki, a zapisuje je proces główny w tej pętli.
    with ProcessPoolExecutor(max_workers=pracownicy) as pula:
        for sciezka, skrot in pula.map(skrot_pliku, kandydaci, chunksize=4):
            zbieracz.dodaj(sciezka, skrot)


def znajdz_duplikaty(
    grupy: dict[int, list[Path]],
    tryb: str = "watki",
    pracownicy: int | None = None,
) -> list[list[Path]]:
    """Zwraca listę grup duplikatów (każda grupa to pliki o identycznej treści).

    Args:
        grupy: wynik grupuj_po_rozmiarze(), czyli rozmiar -> lista plików.
        tryb: "sekwencyjnie", "watki" albo "procesy".
        pracownicy: liczba wątków/procesów; None = wartość domyślna Pythona.
    """
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
