"""Testy skanowania, liczenia skrótów i wątków (skaner.py, skroty.py)."""

import hashlib
import tempfile
import threading
import unittest
from pathlib import Path

from sprzatacz.skaner import filtruj, grupuj_po_rozmiarze, skanuj
from sprzatacz.skroty import TRYBY, ZbieraczWynikow, oblicz_skrot, znajdz_duplikaty


class TestNaFolderze(unittest.TestCase):

    def setUp(self) -> None:
        self.folder = tempfile.TemporaryDirectory()
        self.korzen = Path(self.folder.name)
        (self.korzen / "pod" / "glebiej").mkdir(parents=True)
        self.a = self.korzen / "a.txt"
        self.a_kopia = self.korzen / "pod" / "glebiej" / "a (2).txt"
        self.podobny = self.korzen / "pod" / "b.txt"
        self.a.write_bytes(b"x" * 1000)
        self.a_kopia.write_bytes(b"x" * 1000)
        self.podobny.write_bytes(b"y" * 1000)
        (self.korzen / "inny.txt").write_bytes(b"z" * 10)
        (self.korzen / "smieci.tmp").write_bytes(b"x" * 1000)

    def tearDown(self) -> None:
        self.folder.cleanup()

    def test_skanuj_znajduje_pliki_w_podfolderach(self) -> None:
        nazwy = {plik.sciezka.name for plik in skanuj(self.korzen)}
        self.assertEqual(nazwy, {"a.txt", "a (2).txt", "b.txt", "inny.txt", "smieci.tmp"})

    def test_skanuj_to_generator(self) -> None:
        wynik = skanuj(self.korzen)
        self.assertTrue(hasattr(wynik, "__next__"))

    def test_filtruj_pomija_tymczasowe(self) -> None:
        nazwy = {plik.sciezka.name for plik in filtruj(skanuj(self.korzen))}
        self.assertNotIn("smieci.tmp", nazwy)

    def test_grupuj_po_rozmiarze(self) -> None:
        grupy = grupuj_po_rozmiarze(filtruj(skanuj(self.korzen)))
        self.assertEqual(list(grupy), [1000])
        self.assertEqual(len(grupy[1000]), 3)

    def test_oblicz_skrot_zgodny_z_hashlib(self) -> None:
        self.assertEqual(oblicz_skrot(self.a), hashlib.sha256(b"x" * 1000).hexdigest())

    def test_wszystkie_tryby_daja_ten_sam_wynik(self) -> None:
        grupy = grupuj_po_rozmiarze(filtruj(skanuj(self.korzen)))
        for tryb in TRYBY:
            with self.subTest(tryb=tryb):
                duplikaty = znajdz_duplikaty(grupy, tryb=tryb, pracownicy=2)
                self.assertEqual(len(duplikaty), 1)
                self.assertEqual(set(duplikaty[0]), {self.a, self.a_kopia})

    def test_nieznany_tryb(self) -> None:
        with self.assertRaises(ValueError):
            znajdz_duplikaty({}, tryb="gpu")


class TestZbieraczWynikow(unittest.TestCase):
    def test_lock_nie_gubi_wynikow(self) -> None:
        zbieracz = ZbieraczWynikow()

        def praca() -> None:
            for _ in range(1000):
                zbieracz.dodaj(Path("plik"), "abc")

        watki = [threading.Thread(target=praca) for _ in range(50)]
        for watek in watki:
            watek.start()
        for watek in watki:
            watek.join()

        self.assertEqual(zbieracz.przetworzone, 50_000)
        self.assertEqual(len(zbieracz.po_skrocie["abc"]), 50_000)

    def test_none_nie_trafia_do_wynikow(self) -> None:
        zbieracz = ZbieraczWynikow()
        zbieracz.dodaj(Path("nieczytelny"), None)
        self.assertEqual(zbieracz.przetworzone, 1)
        self.assertEqual(zbieracz.duplikaty(), [])


if __name__ == "__main__":
    unittest.main()
