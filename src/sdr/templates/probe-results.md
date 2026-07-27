---
research: <slug>
date: <YYYY-MM-DD>
stage: probe
verify:
  action: run
  argv: [python, bench.py]
  expect: OK
  environment: clean  # clean | inherit
---

## Resultados por criterio

<!-- Un resultado por cada criterio del brief, referenciado por su ID (C1, C2, ...):
     cumple / no cumple / parcial, con la evidencia que lo respalda. -->
- C1: <cumple|no cumple|parcial> - <evidencia>
- C2: <cumple|no cumple|parcial> - <evidencia>

## Reproducción

<!-- Cómo reproducir la prueba: comandos y/o código versionado en probe/.
     Toda tabla de benchmark debe ir acompañada de su bloque de comandos.
     Ejecutá `sdr verify-probe <slug>` y dejalo en verde antes de avanzar. -->

```bash
# comandos para reproducir el benchmark/POC
python probe/bench.py
```
