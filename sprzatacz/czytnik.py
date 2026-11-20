"""Czytanie pliku kawałkami."""

from pathlib import Path
from types import TracebackType
from typing import Self

DOMYSLNY_KAWALEK = 64 * 1024


class CzytnikPliku:
    """Iterator zwracający kolejne kawałki pliku, obsługuje też with."""

    def __init__(self, sciezka: Path, rozmiar_kawalka: int = DOMYSLNY_KAWALEK) -> None:
        if rozmiar_kawalka <= 0:
            raise ValueError("rozmiar_kawalka musi być większy od zera")
        self.sciezka = sciezka
        self.rozmiar_kawalka = rozmiar_kawalka
        self.przeczytano_bajtow = 0
        self._plik = open(sciezka, "rb")

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> bytes:
        if self._plik.closed:
            raise StopIteration
        kawalek = self._plik.read(self.rozmiar_kawalka)
        if not kawalek:
            self.zamknij()
            raise StopIteration
        self.przeczytano_bajtow += len(kawalek)
        return kawalek

    def zamknij(self) -> None:
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
