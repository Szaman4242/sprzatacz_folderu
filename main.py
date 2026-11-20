"""Sprzątacz folderu: wyszukiwanie zduplikowanych plików."""

import argparse
import logging
import sys
from pathlib import Path

from sprzatacz.raport import Raport
from sprzatacz.skaner import filtruj, grupuj_po_rozmiarze, skanuj
from sprzatacz.skroty import TRYBY, znajdz_duplikaty


def konfiguruj_logowanie(szczegolowo: bool, plik_logu: Path | None) -> None:
    """Logi na ekran, a opcjonalnie także do pliku."""
    ekran = logging.StreamHandler()
    ekran.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    obslugi: list[logging.Handler] = [ekran]

    if plik_logu is not None:
        plik_logu.parent.mkdir(parents=True, exist_ok=True)
        do_pliku = logging.FileHandler(plik_logu, encoding="utf-8")
        do_pliku.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
        obslugi.append(do_pliku)

    logging.basicConfig(level=logging.DEBUG if szczegolowo else logging.INFO,
                        handlers=obslugi)


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
    parser.add_argument("--log", type=Path, default=None,
                        help="zapisuj też komunikaty do pliku (np. wyniki/sprzatacz.log)")
    parser.add_argument("-v", "--verbose", action="store_true", help="więcej komunikatów")
    args = parser.parse_args()

    if args.pracownicy is not None and args.pracownicy < 1:
        parser.error("--pracownicy musi być co najmniej 1")
    if args.raport and args.raport.suffix.lower().lstrip(".") not in Raport.FORMATY:
        parser.error("--raport musi mieć rozszerzenie .txt lub .csv")

    konfiguruj_logowanie(args.verbose, args.log)

    if not args.katalog.is_dir():
        print(f"Błąd: '{args.katalog}' nie jest folderem.", file=sys.stderr)
        return 1

    pliki = filtruj(skanuj(args.katalog), min_rozmiar=args.min_rozmiar)
    grupy = grupuj_po_rozmiarze(pliki)
    liczba_kandydatow = sum(len(sciezki) for sciezki in grupy.values())

    duplikaty = znajdz_duplikaty(grupy, tryb=args.tryb, pracownicy=args.pracownicy)

    raport = Raport(duplikaty, args.katalog)
    print(f"Kandydaci (ten sam rozmiar): {liczba_kandydatow} plików")
    print(raport.podsumowanie())
    if args.verbose:
        print(raport.szczegoly())

    if args.raport:
        raport.format = args.raport.suffix
        try:
            raport.zapisz(args.raport)
        except OSError as blad:
            print(f"Błąd zapisu raportu: {blad}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
