"""Testy iteratora CzytnikPliku (sprzatacz/czytnik.py)."""

import tempfile
import unittest
from pathlib import Path

from sprzatacz.czytnik import CzytnikPliku


class TestCzytnikPliku(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = tempfile.TemporaryDirectory()
        self.plik = Path(self.folder.name) / "dane.bin"
        self.dane = bytes(range(256)) * 10
        self.plik.write_bytes(self.dane)

    def tearDown(self) -> None:
        self.folder.cleanup()

    def test_kawalki_skladaja_sie_w_caly_plik(self) -> None:
        with CzytnikPliku(self.plik, rozmiar_kawalka=1000) as czytnik:
            kawalki = list(czytnik)
        self.assertEqual([len(k) for k in kawalki], [1000, 1000, 560])
        self.assertEqual(b"".join(kawalki), self.dane)

    def test_licznik_przeczytanych_bajtow(self) -> None:
        czytnik = CzytnikPliku(self.plik, rozmiar_kawalka=1000)
        next(czytnik)
        self.assertEqual(czytnik.przeczytano_bajtow, 1000)
        czytnik.zamknij()

    def test_po_koncu_pliku_stopiteration(self) -> None:
        czytnik = CzytnikPliku(self.plik, rozmiar_kawalka=4096)
        next(czytnik)
        with self.assertRaises(StopIteration):
            next(czytnik)
        with self.assertRaises(StopIteration):
            next(czytnik)

    def test_with_zamyka_plik_po_przerwaniu(self) -> None:
        with CzytnikPliku(self.plik, rozmiar_kawalka=100) as czytnik:
            next(czytnik)
        with self.assertRaises(StopIteration):
            next(czytnik)

    def test_iter_zwraca_samego_siebie(self) -> None:
        with CzytnikPliku(self.plik) as czytnik:
            self.assertIs(iter(czytnik), czytnik)

    def test_bledny_rozmiar_kawalka(self) -> None:
        with self.assertRaises(ValueError):
            CzytnikPliku(self.plik, rozmiar_kawalka=0)

    def test_brak_pliku(self) -> None:
        with self.assertRaises(FileNotFoundError):
            CzytnikPliku(Path(self.folder.name) / "nie_ma.bin")


if __name__ == "__main__":
    unittest.main()
