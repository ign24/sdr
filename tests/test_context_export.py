import pytest

from sdr.context_export import export_context_graph
from sdr.context_graph import ContextGraph, GraphEdge, GraphNode, write_context_graph


def _sample_graph() -> ContextGraph:
    return ContextGraph(
        nodes=[
            GraphNode(
                id="criterion:C1", type="criterion", title="C1: métrica", source_files=("brief.md",)
            ),
            GraphNode(
                id="result:C1",
                type="result",
                title="C1 cumple",
                source_files=("probe/results.md",),
                metadata={"status": "cumple", "evidence": "evidencia reproducible"},
            ),
            GraphNode(
                id="decision:recommendation",
                type="decision",
                title="Recomendación",
                source_files=("decision-memo.md",),
                metadata={"ring": "trial"},
            ),
        ],
        edges=[
            GraphEdge(
                source="result:C1",
                target="criterion:C1",
                relation="evaluates",
                provenance="explicit",
            ),
            GraphEdge(
                source="decision:recommendation",
                target="result:C1",
                relation="based_on",
                provenance="explicit",
            ),
        ],
        metadata={"slug": "eval-context"},
    )


def test_export_obsidian_writes_index_notes_frontmatter_and_wikilinks(tmp_path):
    root = tmp_path / "eval-context"
    graph = _sample_graph()
    write_context_graph(graph, root)

    summary = export_context_graph(graph, root, "obsidian")

    out = root / "context" / "obsidian"
    assert summary["format"] == "obsidian"
    assert summary["notes"] == 4
    assert (out / "index.md").exists()
    assert (out / "criterion--C1.md").exists()
    assert (out / "result--C1.md").exists()
    criterion = (out / "criterion--C1.md").read_text(encoding="utf-8")
    result = (out / "result--C1.md").read_text(encoding="utf-8")
    assert "node_id: criterion:C1" in criterion
    assert "node_type: criterion" in criterion
    assert "# C1: métrica" in criterion
    assert "[[result--C1|result:C1]]" in criterion
    assert "[[criterion--C1|criterion:C1]]" in result


def test_export_obsidian_is_deterministic_and_redacts_secrets_and_paths(tmp_path):
    root = tmp_path / "eval-context"
    outside = tmp_path / "secret.env"
    graph = ContextGraph(
        nodes=[
            GraphNode(
                id="source:https-example.com",
                type="source",
                title="API_KEY=abc123",
                source_files=(str(outside),),
                metadata={"summary": "TOKEN: super-secret"},
            )
        ],
        edges=[],
    )
    write_context_graph(graph, root)

    first = export_context_graph(graph, root, "obsidian")
    contents_first = {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted((root / "context" / "obsidian").glob("*.md"))
    }
    second = export_context_graph(graph, root, "obsidian")
    contents_second = {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted((root / "context" / "obsidian").glob("*.md"))
    }

    assert first["warnings"] == second["warnings"] == [f"out-of-scope path: {outside}"]
    assert contents_first == contents_second
    combined = "\n".join(contents_first.values())
    assert "abc123" not in combined
    assert "super-secret" not in combined
    assert "<redacted>" in combined
    assert str(outside) not in combined


def test_export_mermaid_and_dot_write_safe_deterministic_files(tmp_path):
    root = tmp_path / "eval-context"
    graph = _sample_graph()
    write_context_graph(graph, root)

    mermaid = export_context_graph(graph, root, "mermaid")
    dot = export_context_graph(graph, root, "dot")

    mmd_path = root / "context" / "context.mmd"
    dot_path = root / "context" / "context.dot"
    assert mermaid["path"] == str(mmd_path)
    assert dot["path"] == str(dot_path)
    assert mmd_path.read_text(encoding="utf-8").startswith("flowchart TD")
    assert "result:C1" not in mmd_path.read_text(encoding="utf-8").splitlines()[1].split("[")[0]
    dot_text = dot_path.read_text(encoding="utf-8")
    assert dot_text.startswith("digraph context")
    assert 'label="based_on / explicit"' in dot_text
    assert export_context_graph(graph, root, "mermaid")["path"] == mermaid["path"]


def test_export_rejects_context_symlink_escape(tmp_path):
    root = tmp_path / "eval-context"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "context").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="fuera de la raíz"):
        export_context_graph(_sample_graph(), root, "mermaid")

    assert not (outside / "context.mmd").exists()


def test_export_unknown_format_fails(tmp_path):
    graph = _sample_graph()

    try:
        export_context_graph(graph, tmp_path / "eval-context", "bogus")
    except ValueError as exc:
        assert "unsupported export format" in str(exc)
    else:
        raise AssertionError("expected unsupported format failure")
