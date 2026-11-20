"""Sprzątacz folderu – punkt wejścia programu.

Skanuje folder, wybiera pliki o tym samym rozmiarze, liczy dla nich skróty
SHA-256 i wypisuje grupy prawdziwych duplikatów oraz miejsce do odzyskania.

Uruchomienie:
    python main.py dane_testowe
    python main.py dane_testowe --tryb procesy --pracownicy 4
    python main.py dane_testowe --raport wyniki/raport.csv
"""

import argparse
import logging
import sys
from pathlib import Path

from sprzatacz.raport import Raport
from sprzatacz.skaner import filtruj, grupuj_po_rozmiarze, skanuj
from sprzatacz.skroty import TRYBY, znajdz_duplikaty


def main() -> int:
    parser = argparse.ArgumentParser(description="Wyszukiwarka zduplikowanych plików.")
    parser.add_argument("katalog", type=Path, help="folder do przeskanowania")
    parser.add_argument("--min-rozmiar", type=int, default=1,
                        help="pomijaj pliki mniejsze niż podana liczba bajtów")
    parser.add_argument("--tryb", choices=TRYBY, default="watki",
                        help="sposób liczenia skrótów (domyślnie: watki)")
    parser.add_argument("--pracownicy", type=int, default=None,
                        help="liczba wątków lub procesów (domyślnie: automatycznie)")
    parser.add_argument("--raport", type=Path, default=None,
                        help="zapisz raport do pliku .txt lub .csv")
    parser.add_argument("-v", "--verbose", action="store_true", help="więcej komunikatów")
    args = parser.parse_args()

    if args.pracownicy is not None and args.pracownicy < 1:
        parser.error("--pracownicy musi być co najmniej 1")
    if args.raport and args.raport.suffix.lower().lstrip(".") not in Raport.FORMATY:
        parser.error("--raport musi mieć rozszerzenie .txt lub .csv")

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if not args.katalog.is_dir():
        print(f"Błąd: '{args.katalog}' nie jest folderem.", file=sys.stderr)
        return 1

    # Krok 1: potok generatorów – skanowanie, filtrowanie, grupowanie po rozmiarze
    pliki = filtruj(skanuj(args.katalog), min_rozmiar=args.min_rozmiar)
    grupy = grupuj_po_rozmiarze(pliki)
    liczba_kandydatow = sum(len(sciezki) for sciezki in grupy.values())

    # Krok 2: skróty SHA-256 tylko dla kandydatów (czas mierzy dekorator @zmierz_czas)
    duplikaty = znajdz_duplikaty(grupy, tryb=args.tryb, pracownicy=args.pracownicy)

    # Krok 3: raport
    raport = Raport(duplikaty, args.katalog)
    print(f"Kandydaci (ten sam rozmiar): {liczba_kandydatow} plików")
    print(raport.podsumowanie())
    if args.verbose:
        print(raport.szczegoly())

    if args.raport:
        raport.format = args.raport.suffix  # setter @property sprawdza format
        try:
            raport.zapisz(args.raport)
        except OSError as blad:
            print(f"Błąd zapisu raportu: {blad}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
