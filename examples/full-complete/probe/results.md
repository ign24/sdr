---
research: synthetic-full
date: 2026-07-01
stage: probe
verify:
  action: run
  argv: [python, check.py]
  expect: SYNTHETIC_PROBE_OK
  environment: clean
---

## Resultados por criterio
| criterio | resultado | evidencia |
|---|---|---|
| C1 | cumple: tres salidas coinciden | `probe/check.py` |
| C2 | cumple: dos evaluaciones coinciden | `probe/check.py` |

## Reproducción
```bash
python check.py
```
