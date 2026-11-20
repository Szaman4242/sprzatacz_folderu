"""Dekoratory używane w projekcie."""

import functools
import logging
import time
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


def zmierz_czas(funkcja: Callable) -> Callable:
    """Zapisuje w logu czas wykonania funkcji."""

    @functools.wraps(funkcja)
    def opakowanie(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        wynik = funkcja(*args, **kwargs)
        logger.info("Czas wykonania %s: %.2f s", funkcja.__name__, time.perf_counter() - start)
        return wynik

    return opakowanie


def ponow(
    proby: int = 3,
    opoznienie: float = 0.2,
    wyjatki: tuple[type[Exception], ...] = (OSError,),
) -> Callable:
    """Ponawia wywołanie funkcji, gdy rzuci jeden z podanych wyjątków."""
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
                        raise
                    logger.warning(
                        "%s: próba %d/%d nieudana (%s), ponawiam...",
                        funkcja.__name__, numer, proby, blad,
                    )
                    time.sleep(opoznienie)

        return opakowanie

    return dekorator


def wymaga_duplikatow(metoda: Callable) -> Callable:
    """Wywołuje metodę Raportu tylko wtedy, gdy znaleziono duplikaty."""

    @functools.wraps(metoda)
    def opakowanie(self: Any, *args: Any, **kwargs: Any) -> Any:
        if not self.duplikaty:
            logger.info("Brak duplikatów, pomijam %s()", metoda.__name__)
            return None
        return metoda(self, *args, **kwargs)

    return opakowanie
