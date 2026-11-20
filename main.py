"""Sprzątacz folderu – punkt wejścia programu.

Etap 1: skanuje folder i pokazuje grupy plików o tym samym rozmiarze
(kandydatów na duplikaty). Kolejne etapy dodadzą liczenie skrótów SHA-256
i raport z duplikatami.

Uruchomienie:
    python main.py dane_testowe
"""

import argparse
import logging
import sys
from pathlib import Path

from sprzatacz.skaner import filtruj, grupuj_po_rozmiarze, skanuj
from sprzatacz.wzorce import rozpoznaj_kopie


def main() -> int:
    parser = argparse.ArgumentParser(description="Wyszukiwarka zduplikowanych plików.")
    parser.add_argument("katalog", type=Path, help="folder do przeskanowania")
    parser.add_argument("--min-rozmiar", type=int, default=1,
                        help="pomijaj pliki mniejsze niż podana liczba bajtów")
    parser.add_argument("-v", "--verbose", action="store_true", help="więcej komunikatów")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if not args.katalog.is_dir():
        print(f"Błąd: '{args.katalog}' nie jest folderem.", file=sys.stderr)
        return 1

    # Potok generatorów: nic się nie dzieje, dopóki grupuj_po_rozmiarze nie zacznie
    # pobierać plików – wtedy skanuj i filtruj oddają je po jednym.
    pliki = filtruj(skanuj(args.katalog), min_rozmiar=args.min_rozmiar)
    grupy = grupuj_po_rozmiarze(pliki)

    # Wyrażenia generujące (generator expressions) do podsumowania
    liczba_kandydatow = sum(len(sciezki) for sciezki in grupy.values())
    liczba_kopii_z_nazwy = sum(
        1 for sciezki in grupy.values() for s in sciezki if rozpoznaj_kopie(s.name)
    )

    print(f"Grupy plików o tym samym rozmiarze: {len(grupy)}")
    print(f"Kandydaci na duplikaty: {liczba_kandydatow} plików")
    print(f"W tym z nazwą wyglądającą na kopię: {liczba_kopii_z_nazwy}")

    if args.verbose:
        for rozmiar, sciezki in sorted(grupy.items(), reverse=True):
            print(f"\n{rozmiar / 1024:.0f} KB:")
            for sciezka in sciezki:
                print(f"   {sciezka}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
