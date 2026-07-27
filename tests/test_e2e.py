"""E2E: ciclo completo new -> intake -> explore -> probe -> transfer -> reuse -> done.

Ejercita gates, anclaje textual, verificación persistida de probe y aprobación
humana en transfer.
"""

import json
import sys

from sdr import lifecycle, probe_verify
from sdr.research import Approval, Research


def _write(path, text):
    path.write_text(text, encoding="utf-8")


def test_full_cycle_reaches_done(tmp_path):
    r = Research.create(
        base=tmp_path,
        slug="eval-rag",
        title="Evaluar RAG",
        question="¿Sirve RAG agentico para soporte?",
        mode="full",
        owner="nacho",
        timebox=5,
    )

    # --- intake ---
    _write(
        r.artifact_path("brief.md"),
        "---\nresearch: eval-rag\ndate: 2026-07-03\nstage: intake\nowner: nacho\ntimebox: 5\n---\n\n"
        "## Pregunta\n¿RAG agentico mejora la resolucion de soporte?\n\n"
        "## Hipótesis\nCreemos que sube la precision.\n\n"
        "## Contexto\nSoporte con alto volumen.\n\n"
        "## Alcance\nIncluye RAG. No incluye fine-tuning.\n\n"
        "## Criterios de evaluación\n- C1: precision > 0.8\n- C2: latencia < 2s\n\n"
        "## Riesgos de adopción\nCosto de indexado.\n",
    )
    res = lifecycle.advance(r)
    assert res.ok and r.meta.stage == "explore", res.blocked_reason

    # --- explore ---
    _write(
        r.root / "notes" / "landscape.md",
        "---\nresearch: eval-rag\ndate: 2026-07-03\nstage: explore\n"
        "sources:\n"
        "  - id: S1\n    url: https://docs.rag.dev/guide\n    tier: T1\n    date: 2026-01-01\n    alternative: rag-agentico\n"
        "  - id: S2\n    url: https://bench.example.org/rag\n    tier: T2\n    date: 2026-02-01\n    alternative: rag-agentico\n"
        "  - id: S3\n    url: https://docs.search.dev/guide\n    tier: T1\n    date: 2026-01-01\n    alternative: rag-clasico\n"
        "  - id: S4\n    url: https://bench.other.example/rag\n    tier: T2\n    date: 2026-02-01\n    alternative: rag-clasico\n"
        "---\n\n"
        "## Alternativas evaluadas\nRAG clasico vs agentico [S1].\n\n"
        "## Madurez\nEstable [S3].\n\n## Costos\nModerado [S2].\n\n## Riesgos\nDrift de indice.\n\n"
        "## Contra-evidencia\nSe buscaron benchmarks negativos y no aparecieron señales fuertes [S4].\n",
    )
    for source_id, content in {
        "S1": "RAG clasico vs agentico.",
        "S2": "Moderado.",
        "S3": "Estable.",
        "S4": "Se buscaron benchmarks negativos y no aparecieron señales fuertes.",
    }.items():
        source_dir = r.artifact_path(f"notes/sources/{source_id}")
        source_dir.mkdir(parents=True)
        _write(source_dir / "content.md", content)
        urls = {
            "S1": "https://docs.rag.dev/guide",
            "S2": "https://bench.example.org/rag",
            "S3": "https://docs.search.dev/guide",
            "S4": "https://bench.other.example/rag",
        }
        _write(source_dir / "meta.yaml", f"url: {urls[source_id]}\nstatus: ok\n")
    res = lifecycle.advance(r, offline=True)
    assert res.ok and r.meta.stage == "probe", res.blocked_reason

    # --- probe ---
    _write(r.artifact_path("probe/metrics.json"), '{"precision": 0.86, "latency": 1.4}')
    _write(r.artifact_path("probe/bench.py"), "print('OK precision 0.86 latency 1.4')\n")
    _write(
        r.artifact_path("probe/results.md"),
        f"---\nresearch: eval-rag\ndate: 2026-07-03\nstage: probe\nverify:\n  action: run\n  argv: {json.dumps([sys.executable, 'bench.py'])}\n  expect: OK\n---\n\n"
        "## Resultados por criterio\n"
        "| criterio | resultado | evidencia |\n|---|---|---|\n"
        "| C1 | cumple, precision 0.86 | `probe/metrics.json` |\n"
        "| C2 | cumple, 1.4s | `probe/metrics.json` |\n\n"
        "## Reproducción\n```bash\npython bench.py\n```\n",
    )
    verify = probe_verify.verify_probe(r, timeout=5)
    assert verify.passed
    res = lifecycle.advance(r)
    assert res.ok and r.meta.stage == "transfer", res.blocked_reason

    # --- transfer (con aprobación humana) ---
    _write(
        r.artifact_path("decision-memo.md"),
        "---\nresearch: eval-rag\ndate: 2026-07-03\nstage: transfer\nring: trial\naudience: equipo\n---\n\n"
        "## Recomendación\nEn el contexto de soporte, ante el volumen, decidimos pilotar RAG "
        "agentico para lograr mejor precision, porque la prueba cumplió C1 y C2, "
        "aceptando mayor costo de indexado.\n\n"
        "## Alternativas evaluadas\nRAG clasico, fine-tuning.\n\n"
        "## Criterios de selección\nPrecision y latencia.\n\n"
        "## Riesgos y limitaciones\nCosto, drift.\n\n"
        "## Próximos pasos\nPiloto 2 semanas.\n\n"
        "## Audiencia\nEquipo tecnico y direccion.\n",
    )
    # Sin aprobación: bloquea.
    blocked = lifecycle.advance(r)
    assert not blocked.ok and "aprob" in blocked.blocked_reason.lower()

    # Con aprobación humana: avanza a reuse.
    r.meta.approval = Approval(by="nacho", date="2026-07-03")
    r.save()
    res = lifecycle.advance(r)
    assert res.ok and r.meta.stage == "reuse", res.blocked_reason

    # --- reuse ---
    _write(
        r.root / "assets" / "post.md",
        "---\nresearch: eval-rag\ndate: 2026-07-03\nstage: reuse\ntype: post\naudience: external\n---\n\n"
        "RAG agentico subio la precision de soporte a 0.86 en nuestro piloto.\n",
    )
    res = lifecycle.advance(r)
    assert res.ok
    assert r.meta.status == "done"

    # La cadena de validación quedó registrada para todas las etapas del modo full.
    assert set(r.meta.validation) == {"intake", "explore", "probe", "transfer", "reuse"}
    # Y la evidencia sigue consistente (nada fue manipulado tras validar).
    assert lifecycle.check_consistency(r) == []
