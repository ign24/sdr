"""CLI `sdr`: crear investigaciones, validar gates, avanzar etapas y reportar.

La base de investigaciones es `research/` (configurable con la variable de
entorno SDR_ROOT). La salida de cada comando admite `--json` para consumo por
agentes.
"""

from __future__ import annotations

import json as jsonlib
import os
import sys
from datetime import date
from importlib import resources
from pathlib import Path

import click

from sdr import archive as archive_mod
from sdr import audit as audit_mod
from sdr import index as index_mod
from sdr import integration_validation as integration_validation_mod
from sdr import lifecycle, schema, trail
from sdr import probe_verify as probe_verify_mod
from sdr import snapshot as snapshot_mod
from sdr import verification as verification_mod
from sdr.context_export import export_context_graph
from sdr.context_graph import (
    ContextGraphError,
    build_sdr_context_graph,
    inspect_context_graph,
    read_context_graph,
    trace_context_graph,
    write_context_graph,
)
from sdr.context_query import map_query_text_to_intent, query_context_graph
from sdr.gates import check_stage
from sdr.paths import resolve_child, resolve_root, resolve_segment
from sdr.research import META_FILE, Approval, Research

TEMPLATES = resources.files("sdr").joinpath("templates")


def _base() -> Path:
    return resolve_root(os.environ.get("SDR_ROOT", "research"))


def _knowledge_dir() -> Path:
    return resolve_root(os.environ.get("SDR_KNOWLEDGE", "knowledge"))


def _record(research: Research, transition: str, no_commit: bool, paths=None, extra=None) -> None:
    """Registra la transición en el rastro git, degradando con advertencia."""
    if no_commit:
        return
    result = trail.commit_transition(research, transition, paths=paths, extra_paths=extra)
    if result.committed:
        click.echo(f"rastro: {result.message}")
    elif result.warning:
        click.echo(f"rastro: {result.warning}", err=True)


def _load(slug: str) -> Research:
    base = _base()
    try:
        root = resolve_segment(base, slug)
    except ValueError as exc:
        raise click.ClickException(f"slug inválido: {slug!r}") from exc
    if not resolve_child(root, META_FILE).exists():
        raise click.ClickException(f"no existe la investigación {slug!r} en {base}/")
    try:
        return Research.load(root, within=base)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


def _all_research() -> list[Research]:
    base = _base()
    if not base.is_dir():
        return []
    items: list[Research] = []
    for entry in sorted(base.iterdir()):
        child = resolve_segment(base, entry.name)
        if child.is_dir() and resolve_child(child, META_FILE).exists():
            items.append(Research.load(child, within=base))
    return items


def _status_metadata(research: Research) -> dict:
    """Serializa metadata operativa sin exponer el bloque judge histórico."""
    claim_audit = audit_mod.evaluate_claims(research)
    return {
        **{key: value for key, value in research.to_dict().items() if key != "judge"},
        "audit_markers": audit_mod.audit_markers(research),
        "claim_states": claim_audit.states,
        "claim_ledger": claim_audit.ledger,
        "claims_passed": claim_audit.passed,
    }


class _AdvanceCommand(click.Command):
    """Conserva un error de migración para flags retirados sin registrarlos."""

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        if "--override" in args or "--reason" in args:
            raise click.UsageError(
                "--override y --reason fueron retirados de sdr advance; "
                "use sdr resolve-claim para registrar una revisión humana"
            )
        return super().parse_args(ctx, args)


@click.group()
def main() -> None:
    """Spec-Driven Research: harness de I+D aplicada trazable."""


@main.command()
@click.argument("slug")
@click.option("--title", required=True, help="Título de la investigación.")
@click.option("--question", required=True, help="Pregunta de investigación.")
@click.option("--mode", type=click.Choice(schema.MODES), default="full", show_default=True)
@click.option("--owner", default="", help="Responsable de la investigación.")
@click.option("--timebox", type=int, default=0, help="Estimación en días.")
@click.option("--no-commit", is_flag=True, help="No registrar la transición en git.")
@click.option("--json", "as_json", is_flag=True)
def new(
    slug: str,
    title: str,
    question: str,
    mode: str,
    owner: str,
    timebox: int,
    no_commit: bool,
    as_json: bool,
) -> None:
    """Crea una investigación nueva e inicializa su brief."""
    try:
        research = Research.create(
            base=_base(),
            slug=slug,
            title=title,
            question=question,
            mode=mode,
            owner=owner,
            timebox=timebox,
        )
    except (ValueError, FileExistsError) as exc:
        raise click.ClickException(str(exc)) from exc

    brief_template = TEMPLATES.joinpath(schema.template_for("intake"))
    transition_paths = [research.artifact_path(META_FILE)]
    if brief_template.is_file():
        brief_path = research.artifact_path("brief.md")
        brief_path.write_bytes(brief_template.read_bytes())
        transition_paths.append(brief_path)

    _record(research, "new", no_commit, paths=transition_paths)
    if as_json:
        click.echo(jsonlib.dumps(research.to_dict(), ensure_ascii=False, indent=2))
    else:
        click.echo(f"creada investigación {slug!r} en {research.root} (etapa intake)")


@main.command()
@click.argument("slug", required=False)
@click.option("--stage", default=None, help="Validar una etapa específica.")
@click.option("--all", "check_all", is_flag=True, help="Validar todas las investigaciones activas.")
@click.option("--offline", is_flag=True, help="Omitir verificación de enlaces.")
@click.option("--json", "as_json", is_flag=True)
def check(
    slug: str | None, stage: str | None, check_all: bool, offline: bool, as_json: bool
) -> None:
    """Ejecuta el gate de la etapa (capas estructural y evidencial)."""
    if check_all:
        targets = [r for r in _all_research() if r.meta.status == "active"]
    else:
        if not slug:
            raise click.ClickException("indique un <slug> o use --all")
        targets = [_load(slug)]

    reports = []
    ok = True
    for research in targets:
        if (stage or research.meta.stage) == "explore":
            snapshot_mod.ensure_explore_snapshots(research, offline=offline)
        report = check_stage(research, stage=stage, offline=offline)
        consistency = lifecycle.check_consistency(research)
        ok = ok and report.passed and not consistency
        reports.append((research, report, consistency))

    if as_json:
        payload = [
            {**report.to_dict(), "slug": r.meta.slug, "consistency_issues": issues}
            for r, report, issues in reports
        ]
        click.echo(
            jsonlib.dumps(
                payload[0] if len(payload) == 1 else payload, ensure_ascii=False, indent=2
            )
        )
    else:
        for research, report, issues in reports:
            _print_report(research, report, issues)
    sys.exit(0 if ok else 1)


@main.command()
@click.argument("slug")
@click.option("--json", "as_json", is_flag=True)
def snapshot(slug: str, as_json: bool) -> None:
    """Captura snapshots textuales de las fuentes declaradas en notes/."""
    research = _load(slug)
    results = snapshot_mod.capture_declared_sources(research)
    payload = {
        "slug": slug,
        "captured": [result.__dict__ for result in results],
    }
    if as_json:
        click.echo(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
    else:
        click.echo(f"{slug}: {len(results)} fuentes capturadas")
        for result in results:
            click.echo(f"  - {result.source_id}: {result.status} {result.url}")


@main.command("verify-claims")
@click.argument("slug")
@click.option("--json", "as_json", is_flag=True)
def verify_claims(slug: str, as_json: bool) -> None:
    """Ejecuta la verificación anclada claim-vs-fuente sin avanzar etapa."""
    research = _load(slug)
    report = verification_mod.verify_explore_claims(research)
    payload = {
        "schema_version": 2,
        "slug": slug,
        "passed": report.passed,
        "failures": report.failures,
        "items": [item.to_dict() for item in report.items],
    }
    if as_json:
        click.echo(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
    else:
        mark = "OK" if report.passed else "FALLA"
        click.echo(f"[{mark}] verificación anclada de {slug}")
        for item in report.items:
            click.echo(f"  - {item.claim_id} {item.source_id}: {item.state}")
        for failure in report.failures:
            click.echo(f"  x {failure}")
    sys.exit(0 if report.passed else 1)


@main.command("resolve-claim")
@click.argument("slug")
@click.argument("claim_id")
@click.option("--reason", required=True, help="Motivo de la resolución humana.")
@click.option("--by", default=None, help="Autor de la resolución.")
def resolve_claim(slug: str, claim_id: str, reason: str, by: str | None) -> None:
    """Registra resolución humana para un claim no verificable."""
    research = _load(slug)
    try:
        verification_mod.resolve_claim(
            research, claim_id, reason=reason, by=by or os.environ.get("USER", "")
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"{slug}: claim {claim_id} resuelto")


@main.command("verify-probe")
@click.argument("slug")
@click.option("--timeout", type=int, default=300, show_default=True)
@click.option("--json", "as_json", is_flag=True)
def verify_probe(slug: str, timeout: int, as_json: bool) -> None:
    """Ejecuta el comando verify declarado en probe/results.md."""
    research = _load(slug)
    try:
        result = probe_verify_mod.verify_probe(research, timeout=timeout)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    payload = result.to_dict()
    if as_json:
        click.echo(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
    else:
        click.echo(f"comando: {result.command}")
        click.echo(f"resultado: {result.result}")
        if not result.passed:
            click.echo(f"esperado: {result.expect}")
            click.echo(result.output)
    sys.exit(0 if result.passed else 1)


def _print_report(research, report, issues):
    mark = "OK" if report.passed and not issues else "FALLA"
    click.echo(f"[{mark}] {research.meta.slug} (etapa {report.stage})")
    for r in report.results:
        if r.skipped:
            click.echo(f"  - {r.check}: omitido ({r.detail})")
        elif not r.passed:
            click.echo(f"  x {r.check}: {r.detail}")
    for issue in issues:
        click.echo(f"  x consistencia: {issue}")


@main.command(cls=_AdvanceCommand)
@click.argument("slug")
@click.option("--offline", is_flag=True, help="Omitir verificación de enlaces.")
@click.option("--no-commit", is_flag=True, help="No registrar la transición en git.")
def advance(slug: str, offline: bool, no_commit: bool) -> None:
    """Valida la etapa actual y avanza solo si todas las capas pasan."""
    research = _load(slug)
    from_stage = research.meta.stage
    result = lifecycle.advance(research, offline=offline)
    if not result.ok:
        click.echo(f"avance bloqueado: {result.blocked_reason}")
        if result.gate_report:
            _print_report(research, result.gate_report, [])
        sys.exit(1)
    to = research.meta.stage if research.meta.status == "active" else "done"
    _record(
        research,
        f"{from_stage} -> {to}",
        no_commit,
        paths=[research.artifact_path(META_FILE)],
    )
    click.echo(f"{slug}: avanzó a etapa {research.meta.stage} (estado {research.meta.status})")


@main.command()
@click.argument("slug")
@click.option("--stage", default=None, help="Juzgar una etapa específica.")
@click.option("--json", "as_json", is_flag=True)
def judge(slug: str, stage: str | None, as_json: bool) -> None:
    """Tombstone temporal del juez semántico retirado."""
    raise click.ClickException(
        "sdr judge fue retirado; use sdr verify-claims para el anclaje textual "
        "y sdr resolve-claim para registrar una revisión humana"
    )


@main.command()
@click.option("--json", "as_json", is_flag=True)
def doctor(as_json: bool) -> None:
    """Diagnostica la instalación vigente sin inicializar servicios externos."""
    deprecated = sorted(name for name in os.environ if name.startswith("SDR_JUDGE_"))
    payload = {"ready": True, "deprecated_environment": deprecated}
    if as_json:
        click.echo(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
    else:
        click.echo("[OK] instalación SDR")
        for name in deprecated:
            click.echo(f"  deprecada: {name}")


@main.command()
@click.argument("slug")
@click.option("--by", default=None, help="Autor de la aprobación.")
@click.option("--offline", is_flag=True)
def approve(slug: str, by: str | None, offline: bool) -> None:
    """Registra la aprobación humana del decision memo (etapa transfer)."""
    research = _load(slug)
    if research.meta.stage != "transfer":
        raise click.ClickException(
            f"approve solo aplica en etapa transfer; {slug} está en {research.meta.stage}"
        )
    report = check_stage(research, stage="transfer", offline=offline)
    if not report.passed:
        _print_report(research, report, [])
        raise click.ClickException("los gates de transfer deben pasar antes de aprobar")
    research.meta.approval = Approval(
        by=by or os.environ.get("USER", "desconocido"), date=date.today().isoformat()
    )
    research.save()
    click.echo(f"{slug}: aprobado por {research.meta.approval.by}")


@main.command()
@click.argument("slug")
@click.option("--reason", required=True, help="Motivo del descarte.")
@click.option("--no-commit", is_flag=True, help="No registrar la transición en git.")
def drop(slug: str, reason: str, no_commit: bool) -> None:
    """Marca una investigación como descartada conservando su evidencia."""
    research = _load(slug)
    research.meta.status = "dropped"
    research.meta.dropped_reason = reason
    research.save()
    _record(research, "drop", no_commit, paths=[research.artifact_path(META_FILE)])
    click.echo(f"{slug}: descartada ({reason})")


@main.command()
@click.argument("slug")
@click.option("--to", "to_stage", required=True, help="Etapa anterior a la que volver.")
@click.option("--reason", required=True, help="Motivo del retroceso.")
@click.option("--no-commit", is_flag=True, help="No registrar la transición en git.")
def reopen(slug: str, to_stage: str, reason: str, no_commit: bool) -> None:
    """Retrocede a una etapa anterior registrando el motivo (backtracking)."""
    research = _load(slug)
    from_stage = research.meta.stage
    try:
        lifecycle.reopen(research, to=to_stage, reason=reason)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    _record(
        research,
        f"reopen {from_stage} -> {to_stage}",
        no_commit,
        paths=[research.artifact_path(META_FILE)],
    )
    click.echo(f"{slug}: reabierta en etapa {to_stage} ({reason})")


@main.command()
@click.argument("slug")
@click.option("--json", "as_json", is_flag=True)
def migrate(slug: str, as_json: bool) -> None:
    """Migra una investigación v1 a schema_version 2 sin cambiar etapa."""
    research = _load(slug)
    before = research.meta.schema_version
    assigned = snapshot_mod.assign_source_ids(research)
    captured = snapshot_mod.capture_declared_sources(research)
    research.meta.schema_version = 2
    research.save()
    gaps = _migration_gaps(research)
    payload = {
        "slug": slug,
        "from_schema_version": before,
        "to_schema_version": 2,
        "assigned_source_ids": assigned,
        "captured": [item.__dict__ for item in captured],
        "gaps": gaps,
    }
    if as_json:
        click.echo(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
    else:
        click.echo(f"{slug}: migrada a schema_version 2")
        for gap in gaps:
            click.echo(f"  - {gap}")


def _migration_gaps(research: Research) -> list[str]:
    gaps: list[str] = []
    notes_dir = research.artifact_path("notes")
    for path in sorted(notes_dir.glob("*.md")) if notes_dir.is_dir() else []:
        text = path.read_text(encoding="utf-8")
        if "[S" not in text:
            gaps.append(f"{path.name}: faltan citas inline [S<n>]")
        if "## Contra-evidencia" not in text:
            gaps.append(f"{path.name}: falta sección Contra-evidencia")
    return gaps


@main.command()
@click.argument("slug")
@click.option("--no-commit", is_flag=True, help="No registrar la transición en git.")
def archive(slug: str, no_commit: bool) -> None:
    """Consolida una investigación cerrada en knowledge/<slug>.md."""
    research = _load(slug)
    try:
        path = archive_mod.archive_research(research, _knowledge_dir())
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    _record(
        research,
        "archive",
        no_commit,
        paths=[research.artifact_path(META_FILE)],
        extra=[path],
    )
    click.echo(f"{slug}: archivada en {path}")


@main.group()
def context() -> None:
    """Grafo auxiliar no bloqueante de criterios, resultados y decisión.

    Incluye un inventario global de fuentes; no representa lineage completo.
    """


@main.group()
def integrations() -> None:
    """Install packaged integrations into an explicit agent discovery scope."""


@integrations.command("install")
@click.option(
    "--destination",
    required=True,
    type=click.Path(path_type=Path),
    help="Agent skill discovery directory.",
)
@click.option("--json", "as_json", is_flag=True)
def integrations_install(destination: Path, as_json: bool) -> None:
    """Install all packaged canonical skills without overwriting conflicts."""
    try:
        installed = integration_validation_mod.install_canonical_skills(destination)
    except OSError as exc:
        raise click.ClickException(str(exc)) from exc

    payload = {
        "destination": str(destination),
        "installed": [path.name for path in installed],
        "installed_count": len(installed),
    }
    if as_json:
        click.echo(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
    else:
        click.echo(f"installed {len(installed)} canonical skills in {destination}")


@context.command("build")
@click.argument("slug")
@click.option("--json", "as_json", is_flag=True)
def context_build(slug: str, as_json: bool) -> None:
    """Construye `research/<slug>/context/context.json`."""
    research = _load(slug)
    graph = build_sdr_context_graph(research)
    path = write_context_graph(graph, research.root)
    payload = {
        "edges": len(graph.edges),
        "nodes": len(graph.nodes),
        "path": str(path),
        "slug": research.meta.slug,
    }
    if as_json:
        click.echo(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
    else:
        click.echo(
            f"{slug}: context graph escrito en {path} "
            f"({payload['nodes']} nodes, {payload['edges']} edges)"
        )


@context.command("inspect")
@click.argument("slug")
@click.option("--json", "as_json", is_flag=True)
def context_inspect(slug: str, as_json: bool) -> None:
    """Inspecciona métricas y warnings de `context/context.json`."""
    research = _load(slug)
    try:
        graph = read_context_graph(research.root)
    except ContextGraphError as exc:
        raise click.ClickException(str(exc)) from exc
    payload = {"slug": research.meta.slug, **inspect_context_graph(graph)}
    if as_json:
        click.echo(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
    else:
        click.echo(f"Context Graph: {research.meta.slug}")
        click.echo(f"  Nodes: {payload['nodes']}")
        click.echo(f"  Edges: {payload['edges']}")
        click.echo(
            "  Criteria coverage: "
            f"{payload['coverage']['criteria_with_results']}/{payload['coverage']['criteria']}"
        )
        for warning in payload["warnings"]:
            click.echo(f"  warning: {warning}")


@context.command("trace")
@click.argument("slug")
@click.option("--criterion", default="", help="ID de criterio a trazar, por ejemplo C1.")
@click.option("--json", "as_json", is_flag=True)
def context_trace(slug: str, criterion: str, as_json: bool) -> None:
    """Muestra relaciones entrantes y salientes para un nodo del grafo."""
    if not criterion:
        raise click.ClickException("indique --criterion <ID>")
    research = _load(slug)
    try:
        graph = read_context_graph(research.root)
        payload = trace_context_graph(graph, f"criterion:{criterion}")
    except ContextGraphError as exc:
        raise click.ClickException(str(exc)) from exc
    if as_json:
        click.echo(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
    else:
        click.echo(f"Trace: {payload['target']['id']}")
        click.echo("  Incoming:")
        for edge in payload["incoming"]:
            click.echo(f"    {edge['source']} --{edge['relation']}--> {edge['target']}")
        click.echo("  Outgoing:")
        for edge in payload["outgoing"]:
            click.echo(f"    {edge['source']} --{edge['relation']}--> {edge['target']}")


@context.command("check")
@click.argument("slug")
@click.option("--strict", is_flag=True, help="Tratar warnings como fallas.")
@click.option("--json", "as_json", is_flag=True)
def context_check(slug: str, strict: bool, as_json: bool) -> None:
    """Diagnostica estructura y gaps del grafo auxiliar."""
    research = _load(slug)
    try:
        graph = read_context_graph(research.root)
        graph.validate()
    except ContextGraphError as exc:
        payload = {
            "errors": [str(exc)],
            "passed": False,
            "slug": research.meta.slug,
            "warnings": [],
        }
        if as_json:
            click.echo(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
        else:
            click.echo(f"[FALLA] context graph de {slug}")
            click.echo(f"  x {exc}")
        sys.exit(1)

    inspected = inspect_context_graph(graph)
    warnings = inspected["warnings"]
    passed = not strict or not warnings
    payload = {
        "errors": [],
        "passed": passed,
        "slug": research.meta.slug,
        "warnings": warnings,
    }
    if as_json:
        click.echo(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
    else:
        click.echo(f"[{'OK' if passed else 'FALLA'}] context graph de {slug}")
        for warning in warnings:
            click.echo(f"  warning: {warning}")
    sys.exit(0 if passed else 1)


@context.command("export")
@click.argument("slug")
@click.option(
    "--format",
    "export_format",
    type=click.Choice(["obsidian", "mermaid", "dot"]),
    default="obsidian",
    show_default=True,
)
@click.option("--json", "as_json", is_flag=True)
def context_export(slug: str, export_format: str, as_json: bool) -> None:
    """Exporta `context.json` a una vista derivada."""
    research = _load(slug)
    try:
        graph = read_context_graph(research.root)
        payload = {
            "slug": research.meta.slug,
            **export_context_graph(graph, research.root, export_format),
        }
    except (ContextGraphError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    if as_json:
        click.echo(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
    else:
        click.echo(f"{slug}: exported {export_format} context to {payload['path']}")
        for warning in payload.get("warnings", []):
            click.echo(f"  warning: {warning}")


@context.command("query")
@click.argument("slug")
@click.argument("intent")
@click.option("--criterion", default="", help="ID de criterio, por ejemplo C1.")
@click.option("--json", "as_json", is_flag=True)
def context_query(slug: str, intent: str, criterion: str, as_json: bool) -> None:
    """Consulta `context.json` con intents determinísticos."""
    research = _load(slug)
    try:
        graph = read_context_graph(research.root)
        params = {"criterion": criterion}
        if intent not in {
            "why-ring",
            "decision-support",
            "criterion-lineage",
            "gaps",
            "sources-for-result",
        }:
            if " " not in intent:
                raise ContextGraphError(f"unknown query intent: {intent}")
            mapped_intent, mapped_params = map_query_text_to_intent(intent)
            intent = mapped_intent
            params = {**mapped_params, **{key: value for key, value in params.items() if value}}
        payload = {"slug": research.meta.slug, **query_context_graph(graph, intent, **params)}
    except ContextGraphError as exc:
        raise click.ClickException(str(exc)) from exc
    if as_json:
        click.echo(jsonlib.dumps(payload, ensure_ascii=False, indent=2))
    else:
        click.echo(f"Query: {payload['intent']}")
        click.echo("Answer:")
        click.echo(f"  {payload['answer']}")
        click.echo("Involved nodes:")
        for node in payload["involved_nodes"]:
            click.echo(f"  - {node}")
        for warning in payload["warnings"]:
            click.echo(f"warning: {warning}")


@main.command()
@click.argument("slug", required=False)
@click.option("--json", "as_json", is_flag=True)
def status(slug: str | None, as_json: bool) -> None:
    """Muestra el estado de una investigación o el resumen global."""
    if slug:
        research = _load(slug)
        report = check_stage(research, offline=True)
        info = {
            **_status_metadata(research),
            "gate_passed": report.passed,
            "gate_failures": [r.detail for r in report.failures],
            "timebox_overdue": _timebox_overdue(research),
        }
        if as_json:
            click.echo(jsonlib.dumps(info, ensure_ascii=False, indent=2))
        else:
            click.echo(f"{research.meta.slug} — {research.meta.title}")
            click.echo(f"  etapa: {research.meta.stage} | estado: {research.meta.status}")
            click.echo(f"  gate actual: {'OK' if report.passed else 'FALLA'}")
            markers = audit_mod.audit_markers(research)
            if markers:
                click.echo(f"  auditoría: {', '.join(markers)}")
            if _timebox_overdue(research):
                click.echo("  aviso: timebox vencido")
        return

    items = _all_research()
    if as_json:
        click.echo(
            jsonlib.dumps(
                [_status_metadata(r) for r in items],
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    if not items:
        click.echo("no hay investigaciones")
        return
    for r in items:
        m = r.meta
        overdue = " [timebox vencido]" if _timebox_overdue(r) else ""
        markers = audit_mod.audit_markers(r)
        audit = f" [{' ; '.join(markers)}]" if markers else ""
        click.echo(f"{m.slug:24} {m.stage:9} {m.status:8} {m.title}{overdue}{audit}")


def _timebox_overdue(research: Research) -> bool:
    if research.meta.timebox <= 0 or research.meta.status != "active":
        return False
    created = date.fromisoformat(research.meta.created)
    return (date.today() - created).days > research.meta.timebox


@main.command()
def index() -> None:
    """Regenera research/INDEX.md."""
    path = index_mod.write_index(_base())
    click.echo(f"índice regenerado: {path}")


if __name__ == "__main__":
    main()
