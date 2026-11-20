"""Raport z wynikami: podsumowanie, lista duplikatów i zapis do pliku TXT lub CSV."""

import csv
import logging
from pathlib import Path

from sprzatacz.dekoratory import wymaga_duplikatow
from sprzatacz.wzorce import rozpoznaj_kopie

logger = logging.getLogger(__name__)


class Raport:
    """Wyniki wyszukiwania duplikatów.

    Każda grupa duplikatów jest posortowana, a grupy są ułożone od największego
    pliku. W każdej grupie jeden plik oznaczamy do zostawienia, resztę do usunięcia.
    """

    FORMATY = ("txt", "csv")

    def __init__(self, duplikaty: list[list[Path]], katalog: Path) -> None:
        self.katalog = katalog
        self.duplikaty = sorted(
            (sorted(grupa) for grupa in duplikaty),
            key=lambda grupa: grupa[0].stat().st_size,
            reverse=True,
        )
        self._format = "txt"

    @property
    def format(self) -> str:
        """Format pliku raportu: "txt" albo "csv"."""
        return self._format

    @format.setter
    def format(self, wartosc: str) -> None:
        wartosc = wartosc.lower().lstrip(".")  # akceptujemy też ".csv"
        if wartosc not in self.FORMATY:
            raise ValueError(f"Nieobsługiwany format '{wartosc}', dostępne: txt, csv")
        self._format = wartosc

    @property
    def liczba_zbednych(self) -> int:
        """Ile plików można usunąć (wszystkie poza jednym w każdej grupie)."""
        return sum(len(grupa) - 1 for grupa in self.duplikaty)

    @property
    def miejsce_do_odzyskania(self) -> int:
        """Ile bajtów zwolni usunięcie zbędnych kopii."""
        return sum((len(grupa) - 1) * grupa[0].stat().st_size for grupa in self.duplikaty)

    @staticmethod
    def wybierz_oryginal(grupa: list[Path]) -> Path:
        """Wybiera plik do zostawienia: najlepiej taki bez dopisku "(2)" / "- Kopia".

        Jeśli takich plików jest kilka (albo żadnego), wybiera najkrótszą ścieżkę.
        Metoda statyczna, bo nie potrzebuje danych obiektu (self).
        """
        return min(
            grupa,
            key=lambda s: (rozpoznaj_kopie(s.name) is not None, len(str(s)), str(s)),
        )

    def podsumowanie(self) -> str:
        """Kilka linii z najważniejszymi liczbami."""
        return (
            f"Grupy duplikatów (ta sama treść): {len(self.duplikaty)}\n"
            f"Zbędne kopie: {self.liczba_zbednych} plików\n"
            f"Miejsce do odzyskania: {self.miejsce_do_odzyskania / 1024**2:.1f} MB"
        )

    def szczegoly(self) -> str:
        """Lista grup duplikatów z oznaczeniem, który plik zostawić."""
        linie: list[str] = []
        for grupa in self.duplikaty:
            oryginal = self.wybierz_oryginal(grupa)
            linie.append(f"\n{grupa[0].stat().st_size / 1024:.0f} KB:")
            for sciezka in grupa:
                akcja = "ZOSTAW" if sciezka == oryginal else "usuń  "
                linie.append(f"   [{akcja}] {sciezka}")
        return "\n".join(linie)

    @wymaga_duplikatow
    def zapisz(self, sciezka: Path) -> Path:
        """Zapisuje raport do pliku w aktualnym formacie i zwraca jego ścieżkę."""
        sciezka.parent.mkdir(parents=True, exist_ok=True)
        if self.format == "csv":
            self._zapisz_csv(sciezka)
        else:
            tekst = f"Raport dla folderu: {self.katalog}\n\n{self.podsumowanie()}\n{self.szczegoly()}\n"
            sciezka.write_text(tekst, encoding="utf-8")
        logger.info("Zapisano raport: %s", sciezka)
        return sciezka

    def _zapisz_csv(self, sciezka: Path) -> None:
        # utf-8-sig – żeby Excel poprawnie pokazał polskie znaki
        with open(sciezka, "w", newline="", encoding="utf-8-sig") as plik:
            zapis = csv.writer(plik, delimiter=";")
            zapis.writerow(["grupa", "sciezka", "rozmiar_bajty", "akcja"])
            for numer, grupa in enumerate(self.duplikaty, start=1):
                oryginal = self.wybierz_oryginal(grupa)
                for s in grupa:
                    akcja = "zostaw" if s == oryginal else "usun"
                    zapis.writerow([numer, str(s), s.stat().st_size, akcja])
