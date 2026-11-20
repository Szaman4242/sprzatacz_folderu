# Sprzątacz folderu

Program wyszukuje zduplikowane pliki we wskazanym folderze razem z podfolderami i pokazuje, ile miejsca można odzyskać po usunięciu zbędnych kopii. Pliki tymczasowe i systemowe są pomijane. Najpierw pliki są grupowane według rozmiaru, a następnie dla plików o tym samym rozmiarze liczony jest skrót SHA-256. Pliki o identycznym skrócie to duplikaty. Skróty można liczyć sekwencyjnie, w wielu wątkach albo w wielu procesach. Program oznacza też pliki, których nazwa wygląda na kopię, na przykład "raport (2).pdf" albo "raport - Kopia.pdf".

Projekt zaliczeniowy z przedmiotu Zaawansowane techniki programowania w języku Python.

## Uruchomienie

Wymagany Python 3.12 lub nowszy. Projekt nie używa bibliotek zewnętrznych.

| Komenda | Co robi |
|---|---|
| python narzedzia/generuj_dane.py | tworzy folder dane_testowe z plikami testowymi |
| python main.py dane_testowe | skanuje folder i wypisuje podsumowanie |
| python main.py dane_testowe -v | dodatkowo wypisuje grupy duplikatów i pominięte pliki |
| python main.py dane_testowe --tryb sekwencyjnie | liczy skróty plik po pliku |
| python main.py dane_testowe --tryb watki | liczy skróty w wielu wątkach (domyślnie) |
| python main.py dane_testowe --tryb procesy --pracownicy 4 | liczy skróty w 4 procesach |

## Struktura projektu

| Plik | Zawartość |
|---|---|
| main.py | punkt wejścia programu, argumenty wiersza poleceń |
| sprzatacz/wzorce.py | wyrażenia regularne |
| sprzatacz/skaner.py | skanowanie folderu za pomocą generatorów |
| sprzatacz/czytnik.py | iterator czytający plik kawałkami |
| sprzatacz/skroty.py | liczenie skrótów SHA-256 sekwencyjnie, wątkami i procesami |
| narzedzia/generuj_dane.py | generator danych testowych |

## Mapowanie zagadnień

| Zagadnienie | Gdzie w kodzie |
|---|---|
| Generator, yield from | sprzatacz/skaner.py → skanuj() |
| Potok generatorów | sprzatacz/skaner.py → skanuj(), filtruj(), grupuj_po_rozmiarze() |
| Wyrażenia generujące | main.py → main() |
| Regex, walidacja | sprzatacz/wzorce.py → PLIK_POMIJANY_RE |
| Regex, ekstrakcja z grupami nazwanymi | sprzatacz/wzorce.py → KOPIA_RE |
| Iterator | sprzatacz/czytnik.py → klasa CzytnikPliku |
| Wątki, synchronizacja Lock | sprzatacz/skroty.py → _licz_watkami(), klasa ZbieraczWynikow |
| Procesy | sprzatacz/skroty.py → _licz_procesami() |
