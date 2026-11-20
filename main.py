"""Sprzątacz folderu – punkt wejścia programu.

Skanuje folder, wybiera pliki o tym samym rozmiarze, liczy dla nich skróty
SHA-256 i wypisuje grupy prawdziwych duplikatów oraz miejsce do odzyskania.

Uruchomienie:
    python main.py dane_testowe
    python main.py dane_testowe --tryb procesy --pracownicy 4
"""

import argparse
import logging
import sys
import time
from pathlib import Path

from sprzatacz.skaner import filtruj, grupuj_po_rozmiarze, skanuj
from sprzatacz.skroty import TRYBY, znajdz_duplikaty
from sprzatacz.wzorce import rozpoznaj_kopie


def main() -> int:
    parser = argparse.ArgumentParser(description="Wyszukiwarka zduplikowanych plików.")
    parser.add_argument("katalog", type=Path, help="folder do przeskanowania")
    parser.add_argument("--min-rozmiar", type=int, default=1,
                        help="pomijaj pliki mniejsze niż podana liczba bajtów")
    parser.add_argument("--tryb", choices=TRYBY, default="watki",
                        help="sposób liczenia skrótów (domyślnie: watki)")
    parser.add_argument("--pracownicy", type=int, default=None,
                        help="liczba wątków lub procesów (domyślnie: automatycznie)")
    parser.add_argument("-v", "--verbose", action="store_true", help="więcej komunikatów")
    args = parser.parse_args()

    if args.pracownicy is not None and args.pracownicy < 1:
        parser.error("--pracownicy musi być co najmniej 1")

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

    # Krok 2: skróty SHA-256 tylko dla kandydatów, w wybranym trybie
    start = time.perf_counter()
    duplikaty = znajdz_duplikaty(grupy, tryb=args.tryb, pracownicy=args.pracownicy)
    czas = time.perf_counter() - start

    # Podsumowanie – wyrażenia generujące
    liczba_zbednych = sum(len(grupa) - 1 for grupa in duplikaty)
    do_odzyskania = sum((len(grupa) - 1) * grupa[0].stat().st_size for grupa in duplikaty)

    print(f"Kandydaci (ten sam rozmiar): {liczba_kandydatow} plików")
    print(f"Grupy duplikatów (ta sama treść): {len(duplikaty)}")
    print(f"Zbędne kopie: {liczba_zbednych} plików")
    print(f"Miejsce do odzyskania: {do_odzyskania / 1024**2:.1f} MB")
    print(f"Czas liczenia skrótów ({args.tryb}): {czas:.2f} s")

    if args.verbose:
        # największe pliki na górze
        for grupa in sorted(duplikaty, key=lambda g: g[0].stat().st_size, reverse=True):
            print(f"\n{grupa[0].stat().st_size / 1024:.0f} KB:")
            for sciezka in sorted(grupa):
                oznaczenie = "  (kopia)" if rozpoznaj_kopie(sciezka.name) else ""
                print(f"   {sciezka}{oznaczenie}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
