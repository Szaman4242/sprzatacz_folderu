"""Własny iterator czytający plik kawałkami.

Zamiast wczytywać cały plik do pamięci (plik może mieć kilka GB), czytamy go
po kawałku, domyślnie po 64 KB.
"""

from pathlib import Path
from types import TracebackType
from typing import Self

DOMYSLNY_KAWALEK = 64 * 1024  # 64 KB


class CzytnikPliku:
    """Iterator zwracający kolejne kawałki pliku jako bajty.

    Implementuje protokół iteratora: ``__iter__`` i ``__next__``.
    Obsługuje też ``with``, żeby plik został zamknięty nawet wtedy,
    gdy przerwiemy czytanie w połowie.

    Przykład::

        with CzytnikPliku(Path("film.mp4")) as czytnik:
            for kawalek in czytnik:
                ...
    """

    def __init__(self, sciezka: Path, rozmiar_kawalka: int = DOMYSLNY_KAWALEK) -> None:
        if rozmiar_kawalka <= 0:
            raise ValueError("rozmiar_kawalka musi być większy od zera")
        self.sciezka = sciezka
        self.rozmiar_kawalka = rozmiar_kawalka
        self.przeczytano_bajtow = 0
        self._plik = open(sciezka, "rb")  # błąd (np. brak pliku) pojawi się od razu

    def __iter__(self) -> Self:
        """Iterator zwraca samego siebie – dzięki temu działa w pętli for."""
        return self

    def __next__(self) -> bytes:
        """Zwraca następny kawałek pliku albo kończy iterację (StopIteration)."""
        if self._plik.closed:
            raise StopIteration
        kawalek = self._plik.read(self.rozmiar_kawalka)
        if not kawalek:  # koniec pliku
            self.zamknij()
            raise StopIteration
        self.przeczytano_bajtow += len(kawalek)
        return kawalek

    def zamknij(self) -> None:
        """Zamyka plik (można wywołać wielokrotnie)."""
        self._plik.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        typ: type[BaseException] | None,
        wyjatek: BaseException | None,
        slad: TracebackType | None,
    ) -> None:
        self.zamknij()
