"""Generación del índice global de investigaciones (`research/INDEX.md`).

Vista para reporting: una tabla con todas las investigaciones ordenadas por
última actividad. Se regenera, nunca se edita a mano.
"""

from __future__ import annotations

from pathlib import Path

from sdr.audit import audit_markers, evaluate_claims
from sdr.parser import parse_artifact
from sdr.paths import resolve_child, resolve_root, resolve_segment
from sdr.research import META_FILE, Research

INDEX_FILE = "INDEX.md"


def _iter_research(base: Path) -> list[Research]:
    items: list[Research] = []
    for entry in sorted(base.iterdir()):
        child = resolve_segment(base, entry.name)
        if child.is_dir() and resolve_child(child, META_FILE).exists():
            items.append(Research.load(child, within=base))
    return items


def _ring(research: Research) -> str:
    memo = research.artifact_path("decision-memo.md")
    if memo.exists():
        ring = parse_artifact(memo).frontmatter.get("ring")
        if ring:
            return str(ring)
    return "-"


def build_index(base: str | Path) -> str:
    """Construye el markdown del índice para las investigaciones bajo `base`."""
    base = resolve_root(base)
    rows = sorted(_iter_research(base), key=lambda r: r.meta.updated, reverse=True)
    lines = [
        "# Índice de investigaciones",
        "",
        "| Investigación | Título | Modo | Etapa | Estado | "
        "Recomendación | Claims | Ledger | Auditoría | Actividad |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        m = r.meta
        claim_audit = evaluate_claims(r)
        claims = ", ".join(f"{state}:{count}" for state, count in claim_audit.states.items())
        lines.append(
            f"| {m.slug} | {m.title} | {m.mode} | {m.stage} | {m.status} "
            f"| {_ring(r)} | "
            f"{claims or '-'} | {claim_audit.ledger} | "
            f"{', '.join(audit_markers(r)) or '-'} | {m.updated} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_index(base: str | Path) -> Path:
    """Regenera `INDEX.md` en `base` y devuelve su ruta."""
    base = resolve_root(base)
    path = resolve_child(base, INDEX_FILE)
    path.write_text(build_index(base), encoding="utf-8")
    return path
