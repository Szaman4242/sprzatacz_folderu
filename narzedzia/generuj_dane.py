"""Generator danych testowych: oryginały, kopie, pliki podobne i tymczasowe."""

import argparse
import random
import shutil
from pathlib import Path

PODFOLDERY = ["zdjecia", "zdjecia/wakacje", "dokumenty", "dokumenty/stare", "muzyka"]
ROZSZERZENIA = {
    "zdjecia": ".jpg",
    "zdjecia/wakacje": ".jpg",
    "dokumenty": ".pdf",
    "dokumenty/stare": ".docx",
    "muzyka": ".mp3",
}


def nazwa_kopii(sciezka: Path, numer: int) -> str:
    if numer == 1:
        return f"{sciezka.stem} - Kopia{sciezka.suffix}"
    return f"{sciezka.stem} ({numer}){sciezka.suffix}"


def generuj(folder: Path, liczba: int, max_mb: float, ziarno: int) -> None:
    los = random.Random(ziarno)
    if folder.exists():
        shutil.rmtree(folder)

    max_bajtow = int(max_mb * 1024 * 1024)
    oryginaly: list[Path] = []

    for i in range(1, liczba + 1):
        podfolder = los.choice(PODFOLDERY)
        sciezka = folder / podfolder / f"plik_{i:03d}{ROZSZERZENIA[podfolder]}"
        sciezka.parent.mkdir(parents=True, exist_ok=True)
        sciezka.write_bytes(los.randbytes(los.randint(10_000, max_bajtow)))
        oryginaly.append(sciezka)

    liczba_kopii = 0
    for oryginal in los.sample(oryginaly, k=len(oryginaly) * 3 // 10):
        for numer in range(1, los.randint(1, 3) + 1):
            cel = folder / los.choice(PODFOLDERY) if los.random() < 0.3 else oryginal.parent
            cel.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(oryginal, cel / nazwa_kopii(oryginal, numer))
            liczba_kopii += 1

    # ten sam rozmiar, inna treść
    for oryginal in los.sample(oryginaly, k=5):
        rozmiar = oryginal.stat().st_size
        (oryginal.parent / f"podobny_{oryginal.name}").write_bytes(los.randbytes(rozmiar))

    for nazwa in ["~$dokument.docx", "notatki.tmp", "kopia.bak", "Thumbs.db"]:
        (folder / "dokumenty" / nazwa).write_bytes(b"x" * 20_000)

    rozmiar_mb = sum(p.stat().st_size for p in folder.rglob("*") if p.is_file()) / 1024**2
    print(f"Utworzono {liczba} oryginałów i {liczba_kopii} kopii w '{folder}' "
          f"(razem {rozmiar_mb:.1f} MB).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generator danych testowych.")
    parser.add_argument("--folder", type=Path, default=Path("dane_testowe"))
    parser.add_argument("--liczba", type=int, default=100, help="liczba oryginalnych plików")
    parser.add_argument("--max-mb", type=float, default=2.0, help="maks. rozmiar pliku w MB")
    parser.add_argument("--ziarno", type=int, default=42, help="ziarno losowania")
    args = parser.parse_args()

    if args.liczba < 5:
        parser.error("--liczba musi wynosić co najmniej 5")
    generuj(args.folder, args.liczba, args.max_mb, args.ziarno)


if __name__ == "__main__":
    main()
