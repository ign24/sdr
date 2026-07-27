"""Orquestación determinista del avance de etapa.

`advance` ejecuta las capas de validación en orden: estructura/evidencia,
anclaje textual en explore, verificación persistida en probe y aprobación humana
en transfer. Se detiene en el primer fallo y solo entonces mueve la etapa.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from sdr import gates, probe_verify, schema, verification
from sdr import snapshot as snapshot_mod
from sdr.gates import GateReport
from sdr.research import Research


@dataclass
class AdvanceResult:
    ok: bool
    stage: str
    gate_report: GateReport | None = None
    blocked_reason: str = ""


def _stage_files(research: Research, stage: str) -> list[Path]:
    spec = schema.artifact_for(stage, schema_version=research.meta.schema_version)
    if spec.collection_dir:
        directory = research.artifact_path(spec.collection_dir)
        return sorted(directory.glob("*.md")) if directory.is_dir() else []
    path = research.artifact_path(spec.primary_file)
    return [path] if path.exists() else []


def stage_hash(research: Research, stage: str) -> str:
    """Hash sha256 del contenido de los artefactos de la etapa."""
    digest = hashlib.sha256()
    for path in _stage_files(research, stage):
        digest.update(path.read_bytes())
    return digest.hexdigest()


def advance(
    research: Research,
    *,
    offline: bool = False,
) -> AdvanceResult:
    """Valida la etapa actual y avanza solo si todas las capas pasan."""
    stage = research.meta.stage

    consistency_issues = check_consistency(research)
    if consistency_issues:
        return AdvanceResult(
            False,
            stage,
            blocked_reason="consistencia de hashes en rojo: " + "; ".join(consistency_issues),
        )

    if stage == "explore" and research.meta.schema_version >= 2:
        snapshot_mod.ensure_explore_snapshots(research, offline=offline)

    # Capa 1-2: estructura y evidencia.
    report = gates.check_stage(research, stage=stage, offline=offline)
    if not report.passed:
        return AdvanceResult(
            False,
            stage,
            gate_report=report,
            blocked_reason="gates estructurales/evidenciales en rojo",
        )

    # Capa 3: verificación anclada claim-vs-fuente para explore v2.
    if stage == "explore" and research.meta.schema_version >= 2:
        anchored = verification.verify_explore_claims(research)
        if not anchored.passed:
            return AdvanceResult(
                False,
                stage,
                gate_report=report,
                blocked_reason="verificación anclada en rojo: " + "; ".join(anchored.failures),
            )

    # Probe se ejecuta solo mediante `sdr verify-probe`; advance consume su evidencia.
    if stage == "probe":
        stored = research.meta.verify_probe or {}
        current_hash = probe_verify.hash_probe_dir(research)
        if stored.get("result") != "pass":
            return AdvanceResult(
                False,
                stage,
                gate_report=report,
                blocked_reason="falta sdr verify-probe persistido y en verde",
            )
        if stored.get("probe_hash") != current_hash:
            return AdvanceResult(
                False,
                stage,
                gate_report=report,
                blocked_reason="la verificación de probe no está vigente; ejecute sdr verify-probe",
            )

    # Transfer requiere aprobación humana registrada.
    if stage == "transfer" and research.meta.approval is None:
        return AdvanceResult(
            False,
            stage,
            gate_report=report,
            blocked_reason="falta la aprobación humana (sdr approve)",
        )

    # Persistir evidencia de validación y avanzar.
    research.meta.validation[stage] = stage_hash(research, stage)
    research.advance_stage()
    return AdvanceResult(
        True,
        research.meta.stage,
        gate_report=report,
    )


def reopen(research: Research, to: str, reason: str) -> None:
    """Retrocede la investigación a una etapa anterior con motivo registrado.

    Invalida los hashes de validación de la etapa destino y posteriores: esa
    evidencia deberá re-validarse al volver a avanzar. Reactiva investigaciones
    en estado done.
    """
    from datetime import date

    from sdr.research import Reopen

    if not reason.strip():
        raise ValueError("reopen requiere un motivo")
    order = schema.stage_order(research.meta.mode)
    if to not in order:
        raise ValueError(f"etapa {to!r} no pertenece al modo {research.meta.mode!r}")
    current = research.meta.stage
    if order.index(to) >= order.index(current):
        raise ValueError(
            f"reopen solo retrocede: {to!r} no es anterior a la etapa actual {current!r}"
        )
    research.meta.reopens.append(
        Reopen(from_stage=current, to_stage=to, reason=reason, date=date.today().isoformat())
    )
    # La evidencia desde la etapa destino en adelante deja de estar validada.
    for stage in order[order.index(to) :]:
        research.meta.validation.pop(stage, None)
    research.meta.stage = to
    if research.meta.status == "done":
        research.meta.status = "active"
    research.save()


def check_consistency(research: Research) -> list[str]:
    """Detecta etapas cuyo hash validado ya no coincide con el contenido actual."""
    issues: list[str] = []
    for stage, stored in research.meta.validation.items():
        current = stage_hash(research, stage)
        if current != stored:
            issues.append(
                f"etapa {stage!r}: el artefacto cambió tras la validación "
                f"(hash {stored[:8]} != {current[:8]}); re-validá con sdr advance"
            )
    return issues
