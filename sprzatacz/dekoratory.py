"""Własne dekoratory używane w projekcie.

  * zmierz_czas        – dekorator funkcji bez parametrów, mierzy czas wykonania,
  * ponow(proby, ...)  – dekorator funkcji z parametrami, ponawia próbę po błędzie,
  * wymaga_duplikatow  – dekorator metody, korzysta z self (obiektu Raport).
"""

import functools
import logging
import time
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


def zmierz_czas(funkcja: Callable) -> Callable:
    """Wypisuje w logu, ile trwało wykonanie udekorowanej funkcji."""

    @functools.wraps(funkcja)  # zachowuje nazwę i docstring oryginalnej funkcji
    def opakowanie(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        wynik = funkcja(*args, **kwargs)
        czas = time.perf_counter() - start
        logger.info("Czas wykonania %s: %.2f s", funkcja.__name__, czas)
        return wynik

    return opakowanie


def ponow(
    proby: int = 3,
    opoznienie: float = 0.2,
    wyjatki: tuple[type[Exception], ...] = (OSError,),
) -> Callable:
    """Ponawia wywołanie funkcji, jeśli rzuci jeden z podanych wyjątków.

    Dekorator z parametrami ma trzy poziomy funkcji:
    ponow(...) -> dekorator(funkcja) -> opakowanie(*args).

    Args:
        proby: ile razy łącznie próbujemy wywołać funkcję.
        opoznienie: ile sekund czekamy między próbami.
        wyjatki: przy jakich wyjątkach ponawiamy (inne przechodzą od razu dalej).
    """
    if proby < 1:
        raise ValueError("proby musi wynosić co najmniej 1")

    def dekorator(funkcja: Callable) -> Callable:
        @functools.wraps(funkcja)
        def opakowanie(*args: Any, **kwargs: Any) -> Any:
            for numer in range(1, proby + 1):
                try:
                    return funkcja(*args, **kwargs)
                except wyjatki as blad:
                    if numer == proby:
                        raise  # ostatnia próba – przekazujemy błąd dalej
                    logger.warning(
                        "%s: próba %d/%d nieudana (%s), ponawiam...",
                        funkcja.__name__, numer, proby, blad,
                    )
                    time.sleep(opoznienie)

        return opakowanie

    return dekorator


def wymaga_duplikatow(metoda: Callable) -> Callable:
    """Dekorator metody klasy Raport: uruchamia metodę tylko, gdy są duplikaty.

    Pierwszym argumentem opakowania jest ``self``, czyli obiekt, na którym
    wywołano metodę. Dzięki temu dekorator może sprawdzić jego stan.
    """

    @functools.wraps(metoda)
    def opakowanie(self: Any, *args: Any, **kwargs: Any) -> Any:
        if not self.duplikaty:
            logger.info("Brak duplikatów, pomijam %s()", metoda.__name__)
            return None
        return metoda(self, *args, **kwargs)

    return opakowanie
