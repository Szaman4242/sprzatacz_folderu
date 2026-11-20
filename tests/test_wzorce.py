"""Testy wyrażeń regularnych (sprzatacz/wzorce.py)."""

import unittest

from sprzatacz.wzorce import czy_pominac, rozpoznaj_kopie


class TestCzyPominac(unittest.TestCase):
    def test_pliki_tymczasowe_sa_pomijane(self) -> None:
        for nazwa in ["~$raport.docx", "notatki.tmp", "stare.BAK", "plik.swp",
                      "Thumbs.db", "desktop.ini"]:
            with self.subTest(nazwa=nazwa):
                self.assertTrue(czy_pominac(nazwa))

    def test_zwykle_pliki_nie_sa_pomijane(self) -> None:
        for nazwa in ["raport.docx", "zdjecie.jpg", "tmp.txt", "backup.zip"]:
            with self.subTest(nazwa=nazwa):
                self.assertFalse(czy_pominac(nazwa))


class TestRozpoznajKopie(unittest.TestCase):
    def test_kopia_z_numerem(self) -> None:
        info = rozpoznaj_kopie("raport (2).pdf")
        self.assertIsNotNone(info)
        self.assertEqual(info.baza, "raport")
        self.assertEqual(info.numer, 2)
        self.assertEqual(info.rozszerzenie, ".pdf")

    def test_kopia_z_dopiskiem(self) -> None:
        info = rozpoznaj_kopie("zdjecie - Kopia.jpg")
        self.assertIsNotNone(info)
        self.assertEqual(info.baza, "zdjecie")
        self.assertIsNone(info.numer)

    def test_kopia_z_dopiskiem_i_numerem(self) -> None:
        info = rozpoznaj_kopie("plik - Copy (3).txt")
        self.assertEqual((info.baza, info.numer), ("plik", 3))

    def test_zwykla_nazwa_to_nie_kopia(self) -> None:
        self.assertIsNone(rozpoznaj_kopie("raport.pdf"))
        self.assertIsNone(rozpoznaj_kopie("README"))


if __name__ == "__main__":
    unittest.main()
