# Sprzątacz folderu

Program skanuje wskazany folder razem z podfolderami, pomija pliki tymczasowe i systemowe, a pozostałe pliki grupuje według rozmiaru. Grupy z co najmniej dwoma plikami to kandydaci na duplikaty. Program rozpoznaje też pliki, których nazwa wygląda na kopię, na przykład "raport (2).pdf" albo "raport - Kopia.pdf".

Projekt zaliczeniowy z przedmiotu Zaawansowane techniki programowania w języku Python.

## Uruchomienie

Wymagany Python 3.12 lub nowszy. Projekt nie używa bibliotek zewnętrznych.

| Komenda | Co robi |
|---|---|
| python narzedzia/generuj_dane.py | tworzy folder dane_testowe z plikami testowymi |
| python main.py dane_testowe | skanuje folder i wypisuje podsumowanie |
| python main.py dane_testowe -v | dodatkowo wypisuje listę plików i pominięte pliki |

## Struktura projektu

| Plik | Zawartość |
|---|---|
| main.py | punkt wejścia programu, argumenty wiersza poleceń |
| sprzatacz/wzorce.py | wyrażenia regularne |
| sprzatacz/skaner.py | skanowanie folderu za pomocą generatorów |
| narzedzia/generuj_dane.py | generator danych testowych |

## Mapowanie zagadnień

| Zagadnienie | Gdzie w kodzie |
|---|---|
| Generator, yield from | sprzatacz/skaner.py → skanuj() |
| Potok generatorów | sprzatacz/skaner.py → skanuj(), filtruj(), grupuj_po_rozmiarze() |
| Wyrażenia generujące | main.py → main() |
| Regex, walidacja | sprzatacz/wzorce.py → PLIK_POMIJANY_RE |
| Regex, ekstrakcja z grupami nazwanymi | sprzatacz/wzorce.py → KOPIA_RE |
