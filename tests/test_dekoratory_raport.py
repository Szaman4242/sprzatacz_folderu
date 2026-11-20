"""Testy dekoratorów, klasy Raport i Adler-32 z pomiaru GIL."""

import logging
import os
import tempfile
import unittest
import zlib
from pathlib import Path

from benchmarks.gil_benchmark import adler32_python
from sprzatacz.dekoratory import ponow, zmierz_czas
from sprzatacz.raport import Raport


class TestPonow(unittest.TestCase):
    def setUp(self) -> None:
        logging.disable(logging.CRITICAL)

    def tearDown(self) -> None:
        logging.disable(logging.NOTSET)

    def test_udaje_sie_za_trzecim_razem(self) -> None:
        wywolania = []

        @ponow(proby=3, opoznienie=0, wyjatki=(PermissionError,))
        def zablokowany() -> str:
            wywolania.append(1)
            if len(wywolania) < 3:
                raise PermissionError("plik zablokowany")
            return "ok"

        self.assertEqual(zablokowany(), "ok")
        self.assertEqual(len(wywolania), 3)

    def test_po_ostatniej_probie_przekazuje_blad(self) -> None:
        @ponow(proby=2, opoznienie=0, wyjatki=(PermissionError,))
        def zawsze_blad() -> None:
            raise PermissionError

        with self.assertRaises(PermissionError):
            zawsze_blad()

    def test_nie_ponawia_innych_wyjatkow(self) -> None:
        wywolania = []

        @ponow(proby=3, opoznienie=0, wyjatki=(PermissionError,))
        def brak_pliku() -> None:
            wywolania.append(1)
            raise FileNotFoundError

        with self.assertRaises(FileNotFoundError):
            brak_pliku()
        self.assertEqual(len(wywolania), 1)

    def test_bledna_liczba_prob(self) -> None:
        with self.assertRaises(ValueError):
            ponow(proby=0)


class TestZmierzCzas(unittest.TestCase):
    def test_zwraca_wynik_i_zachowuje_nazwe(self) -> None:
        @zmierz_czas
        def dodaj(a: int, b: int) -> int:
            """Dodaje liczby."""
            return a + b

        with self.assertLogs("sprzatacz.dekoratory", level="INFO"):
            self.assertEqual(dodaj(2, 3), 5)
        self.assertEqual(dodaj.__name__, "dodaj")
        self.assertEqual(dodaj.__doc__, "Dodaje liczby.")


class TestRaport(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = tempfile.TemporaryDirectory()
        korzen = Path(self.folder.name)
        self.oryginal = korzen / "foto.jpg"
        self.kopia = korzen / "foto (2).jpg"
        self.kopia2 = korzen / "foto - Kopia.jpg"
        for plik in (self.oryginal, self.kopia, self.kopia2):
            plik.write_bytes(b"a" * 100)
        self.raport = Raport([[self.kopia, self.oryginal, self.kopia2]], korzen)

    def tearDown(self) -> None:
        self.folder.cleanup()

    def test_property(self) -> None:
        self.assertEqual(self.raport.liczba_zbednych, 2)
        self.assertEqual(self.raport.miejsce_do_odzyskania, 200)

    def test_setter_formatu(self) -> None:
        self.raport.format = ".CSV"
        self.assertEqual(self.raport.format, "csv")
        with self.assertRaises(ValueError):
            self.raport.format = "pdf"

    def test_wybierz_oryginal_to_plik_bez_dopisku(self) -> None:
        self.assertEqual(Raport.wybierz_oryginal([self.kopia, self.oryginal]), self.oryginal)

    def test_zapis_csv(self) -> None:
        cel = Path(self.folder.name) / "wyniki" / "raport.csv"
        self.raport.format = "csv"
        self.raport.zapisz(cel)
        linie = cel.read_text(encoding="utf-8-sig").splitlines()
        self.assertEqual(linie[0], "grupa;sciezka;rozmiar_bajty;akcja")
        self.assertEqual(sum(linia.endswith(";zostaw") for linia in linie), 1)

    def test_bez_duplikatow_nie_zapisuje(self) -> None:
        cel = Path(self.folder.name) / "pusty.txt"
        logging.disable(logging.CRITICAL)
        try:
            self.assertIsNone(Raport([], Path(".")).zapisz(cel))
        finally:
            logging.disable(logging.NOTSET)
        self.assertFalse(cel.exists())


class TestAdler32(unittest.TestCase):
    def test_zgodny_z_zlib(self) -> None:
        for dane in [b"", b"Wikipedia", os.urandom(5000)]:
            with self.subTest(dlugosc=len(dane)):
                self.assertEqual(adler32_python(dane), zlib.adler32(dane))


if __name__ == "__main__":
    unittest.main()
