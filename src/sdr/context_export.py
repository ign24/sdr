import json
import shutil
from pathlib import Path
from typing import Any

from sdr.context_graph import (
    ContextGraph,
    GraphEdge,
    GraphNode,
    redact_secret_like_values,
    validate_paths_within_root,
)
from sdr.paths import resolve_child, resolve_root


def export_context_graph(
    graph: ContextGraph, research_path: Path, export_format: str
) -> dict[str, Any]:
    """Export an existing context graph into a derived visual format."""
    research_path = resolve_root(research_path)
    graph.validate()
    if export_format == "obsidian":
        return _export_obsidian(graph, research_path)
    if export_format == "mermaid":
        return _export_mermaid(graph, research_path)
    if export_format == "dot":
        return _export_dot(graph, research_path)
    raise ValueError(f"unsupported export format: {export_format}")


def _export_obsidian(graph: ContextGraph, research_path: Path) -> dict[str, Any]:
    output_dir = resolve_child(research_path, "context/obsidian")
    temp_dir = resolve_child(research_path, "context/obsidian.tmp")
    warnings = _collect_path_warnings(graph, research_path)
    contents = _obsidian_contents(graph, warnings)
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True)
    try:
        for name, text in contents.items():
            (temp_dir / name).write_text(text, encoding="utf-8")
        if output_dir.exists():
            shutil.rmtree(output_dir)
        temp_dir.rename(output_dir)
    except Exception:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        raise
    return {
        "files": len(contents),
        "format": "obsidian",
        "index": str(output_dir / "index.md"),
        "notes": len(contents),
        "path": str(output_dir),
        "warnings": warnings,
    }


def _export_mermaid(graph: ContextGraph, research_path: Path) -> dict[str, Any]:
    path = resolve_child(research_path, "context/context.mmd")
    text = _render_mermaid(graph)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return {"format": "mermaid", "path": str(path), "warnings": []}


def _export_dot(graph: ContextGraph, research_path: Path) -> dict[str, Any]:
    path = resolve_child(research_path, "context/context.dot")
    text = _render_dot(graph)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return {"format": "dot", "path": str(path), "warnings": []}


def _obsidian_contents(graph: ContextGraph, warnings: list[str]) -> dict[str, str]:
    nodes = sorted(graph.nodes, key=lambda node: node.id)
    edges = _sorted_edges(graph.edges)
    names = {node.id: _note_name(node) for node in nodes}
    contents: dict[str, str] = {
        "index.md": _render_obsidian_index(graph, nodes, edges, names, warnings)
    }
    for node in nodes:
        incoming = [edge for edge in edges if edge.target == node.id]
        outgoing = [edge for edge in edges if edge.source == node.id]
        contents[names[node.id]] = _render_obsidian_node(node, incoming, outgoing, names)
    return {name: redact_secret_like_values(text) for name, text in sorted(contents.items())}


def _render_obsidian_index(
    graph: ContextGraph,
    nodes: list[GraphNode],
    edges: list[GraphEdge],
    names: dict[str, str],
    warnings: list[str],
) -> str:
    lines = [
        "---",
        "derived: true",
        "graph_artifact: context/context.json",
        f"slug: {_yaml_scalar(str(graph.metadata.get('slug', '')))}",
        "---",
        "",
        "# SpecLab Context Graph",
        "",
        "> Derived from `context.json`. Regenerate this export instead of editing it as evidence.",
        "",
        f"- Nodes: {len(nodes)}",
        f"- Edges: {len(edges)}",
        "",
        "## Nodes",
    ]
    for node in nodes:
        lines.append(f"- [[{Path(names[node.id]).stem}|{_clean(node.id)}]]")
    if warnings:
        lines.extend(["", "## Warnings"])
        lines.extend("- out-of-scope path omitted" for _warning in warnings)
    return "\n".join(lines) + "\n"


def _render_obsidian_node(
    node: GraphNode,
    incoming: list[GraphEdge],
    outgoing: list[GraphEdge],
    names: dict[str, str],
) -> str:
    safe_sources = [source for source in node.source_files if not Path(source).is_absolute()]
    lines = [
        "---",
        "derived: true",
        "graph_artifact: context/context.json",
        f"node_id: {_clean(node.id)}",
        f"node_type: {_yaml_scalar(_clean(node.type))}",
        "source_files:",
    ]
    lines.extend(f"  - {_yaml_scalar(_clean(source))}" for source in safe_sources)
    lines.extend(
        [
            "---",
            "",
            f"# {_clean(node.title)}",
            "",
            "## Metadata",
            "",
            "```json",
            _clean(json.dumps(node.metadata, ensure_ascii=False, indent=2, sort_keys=True)),
            "```",
            "",
            "## Outgoing links",
        ]
    )
    lines.extend(_edge_line(edge, edge.target, names) for edge in outgoing)
    if not outgoing:
        lines.append("- none")
    lines.append("")
    lines.append("## Incoming links")
    lines.extend(_edge_line(edge, edge.source, names) for edge in incoming)
    if not incoming:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def _render_mermaid(graph: ContextGraph) -> str:
    aliases = _aliases(graph.nodes)
    lines = ["flowchart TD"]
    for node in sorted(graph.nodes, key=lambda item: item.id):
        lines.append(f'  {aliases[node.id]}["{_mermaid_label(node.title)}"]')
    for edge in _sorted_edges(graph.edges):
        label = _mermaid_label(f"{edge.relation} / {edge.provenance}")
        lines.append(f"  {aliases[edge.source]} -->|{label}| {aliases[edge.target]}")
    return "\n".join(lines) + "\n"


def _render_dot(graph: ContextGraph) -> str:
    aliases = _aliases(graph.nodes)
    lines = ["digraph context {"]
    for node in sorted(graph.nodes, key=lambda item: item.id):
        lines.append(f'  {aliases[node.id]} [label="{_dot_label(node.title)}"];')
    for edge in _sorted_edges(graph.edges):
        label = _dot_label(f"{edge.relation} / {edge.provenance}")
        lines.append(f'  {aliases[edge.source]} -> {aliases[edge.target]} [label="{label}"];')
    lines.append("}")
    return "\n".join(lines) + "\n"


def _edge_line(edge: GraphEdge, linked_node: str, names: dict[str, str]) -> str:
    stem = Path(names[linked_node]).stem
    return f"- {edge.relation} / {edge.provenance}: [[{stem}|{_clean(linked_node)}]]"


def _note_name(node: GraphNode) -> str:
    raw = node.id.split(":", 1)[1] if ":" in node.id else node.id
    safe = "".join(char if char.isalnum() or char in "._-" else "-" for char in raw).strip("-")
    while "--" in safe:
        safe = safe.replace("--", "-")
    return f"{node.type}--{safe or 'node'}.md"


def _aliases(nodes: list[GraphNode]) -> dict[str, str]:
    return {
        node.id: f"n{index}"
        for index, node in enumerate(sorted(nodes, key=lambda item: item.id), 1)
    }


def _sorted_edges(edges: list[GraphEdge]) -> list[GraphEdge]:
    return sorted(
        edges, key=lambda edge: (edge.source, edge.relation, edge.target, edge.provenance)
    )


def _collect_path_warnings(graph: ContextGraph, research_path: Path) -> list[str]:
    paths: list[str] = []
    for node in graph.nodes:
        paths.extend(node.source_files)
    return validate_paths_within_root(research_path, tuple(paths))


def _clean(value: str) -> str:
    return redact_secret_like_values(value)


def _yaml_scalar(value: str) -> str:
    if not value:
        return "''"
    if any(char in value for char in ':#[]{}\n"'):
        return json.dumps(value, ensure_ascii=False)
    return value


def _mermaid_label(value: str) -> str:
    return _clean(value).replace('"', "'").replace("|", "/")


def _dot_label(value: str) -> str:
    return _clean(value).replace("\\", "\\\\").replace('"', '\\"')
