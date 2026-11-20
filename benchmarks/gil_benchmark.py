"""Pomiar wpływu GIL: sekwencyjnie vs wątki vs procesy.

Mierzymy dwa zadania wykonywane dla każdego pliku z folderu:

  1. SHA-256 przez hashlib – to samo, co robi program. Liczenie odbywa się
     w kodzie C, który na ten czas ZWALNIA GIL.
  2. Adler-32 napisany w czystym Pythonie – pętla po bajtach. Interpreter
     wykonuje każdą instrukcję i przez cały czas TRZYMA GIL.

Uruchomienie (z głównego folderu projektu):
    python -m benchmarks.gil_benchmark
    python -m benchmarks.gil_benchmark --powtorzenia 5 --pracownicy 8
"""

import argparse
import functools
import os
import statistics
import sys
import time
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path

from sprzatacz.czytnik import CzytnikPliku
from sprzatacz.skaner import filtruj, skanuj
from sprzatacz.skroty import TRYBY, oblicz_skrot

SHA = "SHA-256 (hashlib, C)"
ADLER = "Adler-32 (czysty Python)"


def adler32_python(dane: bytes) -> int:
    """Suma kontrolna Adler-32 liczona w czystym Pythonie.

    Daje ten sam wynik co zlib.adler32(dane), ale każdy bajt przechodzi przez
    interpreter Pythona, więc zadanie przez cały czas trzyma GIL.
    """
    a, b = 1, 0
    for bajt in dane:
        a = (a + bajt) % 65521
        b = (b + a) % 65521
    return (b << 16) | a


def adler32_pliku(sciezka: Path, limit_bajtow: int) -> int:
    """Liczy adler32_python() dla pierwszych ``limit_bajtow`` bajtów pliku."""
    dane = bytearray()
    with CzytnikPliku(sciezka) as czytnik:
        for kawalek in czytnik:
            dane += kawalek
            if len(dane) >= limit_bajtow:
                break
    return adler32_python(bytes(dane[:limit_bajtow]))


def uruchom(zadanie: Callable[[Path], object], pliki: list[Path], tryb: str,
            pracownicy: int) -> float:
    """Wykonuje zadanie dla wszystkich plików w danym trybie i zwraca czas w sekundach.

    Czas obejmuje też utworzenie puli wątków/procesów – tak jak w prawdziwym programie.
    """
    start = time.perf_counter()
    if tryb == "sekwencyjnie":
        list(map(zadanie, pliki))
    elif tryb == "watki":
        with ThreadPoolExecutor(max_workers=pracownicy) as pula:
            list(pula.map(zadanie, pliki))
    else:
        with ProcessPoolExecutor(max_workers=pracownicy) as pula:
            list(pula.map(zadanie, pliki, chunksize=4))
    return time.perf_counter() - start


def zmierz(pliki: list[Path], powtorzenia: int, pracownicy: int,
           limit_bajtow: int) -> dict[str, dict[str, float]]:
    """Zwraca medianę czasów: wyniki[zadanie][tryb] = sekundy."""
    zadania: dict[str, Callable[[Path], object]] = {
        SHA: oblicz_skrot,
        # partial "przypina" limit_bajtow; obiekt partial da się przesłać do procesu
        ADLER: functools.partial(adler32_pliku, limit_bajtow=limit_bajtow),
    }
    wyniki: dict[str, dict[str, float]] = {}
    for nazwa, zadanie in zadania.items():
        wyniki[nazwa] = {}
        for tryb in TRYBY:
            czasy = [uruchom(zadanie, pliki, tryb, pracownicy) for _ in range(powtorzenia)]
            wyniki[nazwa][tryb] = statistics.median(czasy)
            print(f"  {nazwa:<26} {tryb:<13} {wyniki[nazwa][tryb]:7.3f} s")
    return wyniki


def tabela_markdown(wyniki: dict[str, dict[str, float]]) -> str:
    """Tabela wyników w formacie Markdown (do wklejenia w README)."""
    linie = ["| Zadanie | Tryb | Czas [s] | Przyspieszenie |", "|---|---|---|---|"]
    for zadanie, czasy in wyniki.items():
        for tryb, czas in czasy.items():
            przyspieszenie = czasy["sekwencyjnie"] / czas
            linie.append(f"| {zadanie} | {tryb} | {czas:.3f} | {przyspieszenie:.2f}× |")
    return "\n".join(linie)


def rysuj_wykres(wyniki: dict[str, dict[str, float]], sciezka: Path, opis: str) -> bool:
    """Rysuje wykres przyspieszeń. Zwraca False, jeśli brak biblioteki matplotlib."""
    try:
        import matplotlib
        matplotlib.use("Agg")  # rysowanie do pliku, bez okna
        import matplotlib.pyplot as plt
    except ImportError:
        return False

    tlo, tekst, siatka = "#fcfcfb", "#3d3d3a", "#e5e4df"
    kolory = {"sekwencyjnie": "#2a78d6", "watki": "#eb6834", "procesy": "#1baf7a"}
    zadania = list(wyniki)
    szerokosc = 0.26

    fig, ax = plt.subplots(figsize=(8, 4.8), facecolor=tlo)
    ax.set_facecolor(tlo)
    for i, tryb in enumerate(TRYBY):
        x = [n + (i - 1) * szerokosc for n in range(len(zadania))]
        y = [wyniki[z]["sekwencyjnie"] / wyniki[z][tryb] for z in zadania]
        slupki = ax.bar(x, y, width=szerokosc, color=kolory[tryb], label=tryb,
                        edgecolor=tlo, linewidth=2, zorder=3)
        ax.bar_label(slupki, labels=[f"{v:.1f}×" for v in y], padding=3,
                     color=tekst, fontsize=9)

    ax.set_xticks(range(len(zadania)), zadania, color=tekst)
    ax.set_ylabel("Przyspieszenie względem wersji sekwencyjnej", color=tekst)
    ax.set_title(f"Wpływ GIL: wątki a procesy\n{opis}", color=tekst, fontsize=11)
    ax.axhline(1, color=tekst, linewidth=1, linestyle="--", zorder=2)
    ax.grid(axis="y", color=siatka, zorder=0)
    ax.tick_params(colors=tekst)
    for strona in ("top", "right", "left"):
        ax.spines[strona].set_visible(False)
    ax.legend(frameon=False, labelcolor=tekst)
    fig.tight_layout()

    sciezka.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(sciezka, dpi=150, facecolor=tlo)
    plt.close(fig)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Pomiar wpływu GIL.")
    parser.add_argument("--dane", type=Path, default=Path("dane_testowe"),
                        help="folder z plikami do pomiaru")
    parser.add_argument("--powtorzenia", type=int, default=3,
                        help="ile razy powtórzyć każdy pomiar (liczy się mediana)")
    parser.add_argument("--pracownicy", type=int, default=os.cpu_count() or 4,
                        help="liczba wątków i procesów")
    parser.add_argument("--limit-kb", type=int, default=64,
                        help="ile KB z każdego pliku liczy Adler-32 w czystym Pythonie")
    parser.add_argument("--wyniki", type=Path, default=Path("wyniki"),
                        help="folder na tabelę i wykres")
    args = parser.parse_args()

    if args.powtorzenia < 1 or args.pracownicy < 1 or args.limit_kb < 1:
        parser.error("--powtorzenia, --pracownicy i --limit-kb muszą być większe od zera")
    if not args.dane.is_dir():
        parser.error(f"'{args.dane}' nie jest folderem (uruchom narzedzia/generuj_dane.py)")

    pliki = [plik.sciezka for plik in filtruj(skanuj(args.dane))]
    if not pliki:
        parser.error(f"W folderze '{args.dane}' nie ma plików")

    gil = getattr(sys, "_is_gil_enabled", lambda: True)()  # funkcja jest od Pythona 3.13
    opis = (f"Python {sys.version.split()[0]}, GIL {'włączony' if gil else 'wyłączony'}, "
            f"{os.cpu_count()} rdzeni logicznych, {args.pracownicy} pracowników")
    print(f"{opis}\nPlików: {len(pliki)}, powtórzeń: {args.powtorzenia}")

    # Rozgrzewka: pierwszy odczyt idzie z dysku, kolejne z pamięci podręcznej systemu.
    # Bez tego pierwszy mierzony tryb byłby niesprawiedliwie wolniejszy.
    print("Rozgrzewka...")
    uruchom(oblicz_skrot, pliki, "sekwencyjnie", args.pracownicy)

    print("Pomiar (mediana):")
    wyniki = zmierz(pliki, args.powtorzenia, args.pracownicy, args.limit_kb * 1024)

    tabela = tabela_markdown(wyniki)
    print("\n" + tabela)
    args.wyniki.mkdir(parents=True, exist_ok=True)
    (args.wyniki / "gil_benchmark.md").write_text(f"{opis}\n\n{tabela}\n", encoding="utf-8")

    wykres = args.wyniki / "gil_benchmark.png"
    if rysuj_wykres(wyniki, wykres, opis):
        print(f"\nZapisano: {args.wyniki / 'gil_benchmark.md'} oraz {wykres}")
    else:
        print("\nBrak matplotlib – pomijam wykres (pip install -r requirements.txt).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
