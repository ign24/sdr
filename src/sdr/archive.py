"""Archivado: consolida una investigación cerrada en la base de conocimiento.

El archive es el equivalente al archive de OpenSpec: la investigación terminada
deja de ser una carpeta suelta y se convierte en un asset consultable en
`knowledge/<slug>.md`, con la síntesis (pregunta, recomendación, ring,
resultados) y el enlace a la evidencia completa.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from sdr.audit import evaluate_claims
from sdr.parser import parse_artifact
from sdr.paths import resolve_child, resolve_root
from sdr.research import Research
from sdr.verification_ledger import load_ledger


def archive_research(research: Research, knowledge_dir: str | Path) -> Path:
    """Escribe la síntesis en `knowledge/<slug>.md` y marca la investigación."""
    if research.meta.status not in ("done", "dropped"):
        raise ValueError(
            f"solo se archivan investigaciones done o dropped; "
            f"{research.meta.slug!r} está {research.meta.status!r}"
        )
    claim_audit = evaluate_claims(research)
    if claim_audit.has_claims and not claim_audit.passed:
        persisted = research.artifact_path("notes/sources/verification.yaml")
        detail = (
            "obsoleto"
            if claim_audit.ledger != "current"
            and persisted.exists()
            and load_ledger(persisted)["claims"]
            else "pendiente"
        )
        raise ValueError(f"ledger de claims {detail}; ejecute sdr verify-claims antes de archivar")
    knowledge_dir = resolve_root(knowledge_dir)
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    path = resolve_child(knowledge_dir, f"{research.meta.slug}.md")
    path.write_text(_synthesis(research), encoding="utf-8")
    research.meta.archived = True
    research.save()
    return path


def _section_from(research: Research, relative: str, section: str) -> str:
    artifact_path = research.artifact_path(relative)
    if not artifact_path.exists():
        return ""
    return parse_artifact(artifact_path).section(section) or ""


def _ring(research: Research) -> str:
    memo = research.artifact_path("decision-memo.md")
    if memo.exists():
        return str(parse_artifact(memo).frontmatter.get("ring", "-"))
    return "-"


def _synthesis(research: Research) -> str:
    meta = research.meta
    lines = [
        "---",
        f"research: {meta.slug}",
        f"question: {meta.question}",
        f"status: {meta.status}",
        f"ring: {_ring(research)}",
        f"archived: {date.today().isoformat()}",
        "---",
        "",
        f"# {meta.title}",
        "",
        f"**Pregunta:** {meta.question}",
        "",
    ]
    if meta.status == "dropped":
        lines += ["## Motivo de descarte", "", meta.dropped_reason or "(sin motivo)", ""]
    recommendation = _section_from(research, "decision-memo.md", "Recomendación")
    if recommendation:
        lines += ["## Recomendación", "", recommendation, ""]
    results = _section_from(research, "probe/results.md", "Resultados por criterio")
    if results:
        lines += ["## Resultados por criterio", "", results, ""]
    risks = _section_from(research, "decision-memo.md", "Riesgos y limitaciones")
    if risks:
        lines += ["## Riesgos y limitaciones", "", risks, ""]
    if meta.reopens:
        lines += ["## Reopens", ""]
        lines += [f"- {r.date}: {r.from_stage} -> {r.to_stage} ({r.reason})" for r in meta.reopens]
        lines.append("")
    claim_states = evaluate_claims(research).states
    if claim_states:
        lines += ["## Estado de claims", ""]
        lines += [f"- {state}: {count}" for state, count in claim_states.items()]
        lines.append("")
    lines += [
        "## Evidencia completa",
        "",
        f"Ver `research/{meta.slug}/` (brief, notas, probe, decision memo y assets).",
        "",
    ]
    return "\n".join(lines)
