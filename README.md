# Sprzątacz folderu

Program wyszukuje zduplikowane pliki we wskazanym folderze razem z podfolderami i pokazuje, ile miejsca można odzyskać po usunięciu zbędnych kopii. Pliki tymczasowe i systemowe są pomijane. Najpierw pliki są grupowane według rozmiaru, a następnie dla plików o tym samym rozmiarze liczony jest skrót SHA-256. Pliki o identycznym skrócie to duplikaty. Skróty można liczyć sekwencyjnie, w wielu wątkach albo w wielu procesach. W każdej grupie program wskazuje plik do zostawienia, czyli ten, którego nazwa nie wygląda na kopię (na przykład "raport.pdf" zamiast "raport (2).pdf" albo "raport - Kopia.pdf"). Wynik można zapisać do raportu w formacie TXT lub CSV.

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
| python main.py dane_testowe --raport wyniki/raport.txt | zapisuje raport tekstowy |
| python main.py dane_testowe --raport wyniki/raport.csv | zapisuje raport CSV (do otwarcia w Excelu) |

## Struktura projektu

| Plik | Zawartość |
|---|---|
| main.py | punkt wejścia programu, argumenty wiersza poleceń |
| sprzatacz/wzorce.py | wyrażenia regularne |
| sprzatacz/skaner.py | skanowanie folderu za pomocą generatorów |
| sprzatacz/czytnik.py | iterator czytający plik kawałkami |
| sprzatacz/skroty.py | liczenie skrótów SHA-256 sekwencyjnie, wątkami i procesami |
| sprzatacz/dekoratory.py | własne dekoratory funkcji i metod |
| sprzatacz/raport.py | klasa Raport, zapis wyników do TXT i CSV |
| narzedzia/generuj_dane.py | generator danych testowych |

## Mapowanie zagadnień

| Zagadnienie | Gdzie w kodzie |
|---|---|
| Generator, yield from | sprzatacz/skaner.py → skanuj() |
| Potok generatorów | sprzatacz/skaner.py → skanuj(), filtruj(), grupuj_po_rozmiarze() |
| Wyrażenia generujące | main.py → main(), sprzatacz/raport.py → Raport.liczba_zbednych, Raport.miejsce_do_odzyskania |
| Regex, walidacja | sprzatacz/wzorce.py → PLIK_POMIJANY_RE |
| Regex, ekstrakcja z grupami nazwanymi | sprzatacz/wzorce.py → KOPIA_RE |
| Iterator | sprzatacz/czytnik.py → klasa CzytnikPliku |
| Wątki, synchronizacja Lock | sprzatacz/skroty.py → _licz_watkami(), klasa ZbieraczWynikow |
| Procesy | sprzatacz/skroty.py → _licz_procesami() |
| Dekorator funkcji, functools.wraps | sprzatacz/dekoratory.py → zmierz_czas, użyty na skroty.py → znajdz_duplikaty() |
| Dekorator z parametrami | sprzatacz/dekoratory.py → ponow(proby, opoznienie, wyjatki), użyty na skroty.py → oblicz_skrot() |
| Dekorator metody korzystający z self | sprzatacz/dekoratory.py → wymaga_duplikatow, użyty na raport.py → Raport.zapisz() |
| @property z setterem | sprzatacz/raport.py → Raport.format |
| @property | sprzatacz/raport.py → Raport.liczba_zbednych, Raport.miejsce_do_odzyskania |
| @staticmethod | sprzatacz/raport.py → Raport.wybierz_oryginal() |
