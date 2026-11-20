Python 3.12.3, GIL włączony, 20 rdzeni logicznych, 20 pracowników

| Zadanie | Tryb | Czas [s] | Przyspieszenie |
|---|---|---|---|
| SHA-256 (hashlib, C) | sekwencyjnie | 0.118 | 1.00× |
| SHA-256 (hashlib, C) | watki | 0.051 | 2.31× |
| SHA-256 (hashlib, C) | procesy | 0.393 | 0.30× |
| Adler-32 (czysty Python) | sekwencyjnie | 0.679 | 1.00× |
| Adler-32 (czysty Python) | watki | 0.694 | 0.98× |
| Adler-32 (czysty Python) | procesy | 0.439 | 1.55× |
