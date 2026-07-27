import httpx
import pytest

from sdr.network_policy import NetworkPolicyError
from sdr.parser import parse_artifact
from sdr.research import Research
from sdr.snapshot import FetchResult, assign_source_ids, capture_source_snapshot, fetch_url

PUBLIC_IP = "93.184.216.34"


def _public_resolver(host: str):
    return [PUBLIC_IP]


def test_capture_source_snapshot_persists_meta_and_content(tmp_path):
    r = Research.create(base=tmp_path, slug="eval-foo", title="Evaluar Foo", question="¿Q?")

    def fetcher(url: str) -> FetchResult:
        return FetchResult(
            url=url,
            status_code=200,
            text="<html><head><title>Doc Foo</title></head><body><main>Foo soporta modo offline.</main></body></html>",
        )

    result = capture_source_snapshot(
        r,
        source_id="S1",
        url="https://docs.foo.dev/guide",
        fetcher=fetcher,
    )

    meta_path = r.root / "notes" / "sources" / "S1" / "meta.yaml"
    content_path = r.root / "notes" / "sources" / "S1" / "content.md"
    assert result.status == "ok"
    assert result.content_hash
    assert meta_path.exists()
    assert content_path.read_text(encoding="utf-8") == "Foo soporta modo offline.\n"
    meta_text = meta_path.read_text(encoding="utf-8")
    assert "url: https://docs.foo.dev/guide" in meta_text
    assert "title: Doc Foo" in meta_text
    assert "http_status: 200" in meta_text
    assert "org: foo" in meta_text
    assert "status: ok" in meta_text


def test_capture_source_snapshot_marks_empty_content_unverifiable(tmp_path):
    r = Research.create(base=tmp_path, slug="eval-foo", title="Evaluar Foo", question="¿Q?")

    def fetcher(url: str) -> FetchResult:
        return FetchResult(url=url, status_code=200, text="<html><title>Paywall</title></html>")

    result = capture_source_snapshot(
        r,
        source_id="S2",
        url="https://example.com/paywall",
        fetcher=fetcher,
    )

    meta_path = r.root / "notes" / "sources" / "S2" / "meta.yaml"
    content_path = r.root / "notes" / "sources" / "S2" / "content.md"
    assert result.status == "unverifiable"
    assert content_path.read_text(encoding="utf-8") == ""
    assert "status: unverifiable" in meta_path.read_text(encoding="utf-8")


def test_fetch_url_rejects_response_larger_than_limit_without_buffering_it():
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                headers={"content-type": "text/html"},
                content=b"x" * 11,
            )
        )
    )

    with pytest.raises(NetworkPolicyError, match="tamaño máximo"):
        fetch_url(
            "https://public.example/large",
            client=client,
            resolver=_public_resolver,
            max_response_bytes=10,
        )


def test_fetch_url_rejects_unsupported_content_type():
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                headers={"content-type": "application/octet-stream"},
                content=b"binary",
            )
        )
    )

    with pytest.raises(NetworkPolicyError, match="content-type no soportado"):
        fetch_url(
            "https://public.example/file",
            client=client,
            resolver=_public_resolver,
        )


def test_assign_source_ids_preserves_declaration_order(tmp_path):
    r = Research.create(base=tmp_path, slug="eval-foo", title="Evaluar Foo", question="¿Q?")
    note = r.root / "notes" / "n1.md"
    note.write_text(
        "---\n"
        "research: eval-foo\n"
        "date: 2026-07-03\n"
        "stage: explore\n"
        "sources:\n"
        "  - url: https://a.example.com\n    tier: T1\n    date: 2026-01-01\n"
        "  - url: https://b.example.com\n    tier: T2\n    date: 2026-01-02\n"
        "---\n\n"
        "## Alternativas evaluadas\nFoo.\n",
        encoding="utf-8",
    )

    changed = assign_source_ids(r)

    sources = parse_artifact(note).frontmatter["sources"]
    assert changed == 2
    assert [source["id"] for source in sources] == ["S1", "S2"]


def test_assign_source_ids_keeps_existing_ids_and_fills_gaps(tmp_path):
    r = Research.create(base=tmp_path, slug="eval-foo", title="Evaluar Foo", question="¿Q?")
    note = r.root / "notes" / "n1.md"
    note.write_text(
        "---\n"
        "research: eval-foo\n"
        "date: 2026-07-03\n"
        "stage: explore\n"
        "sources:\n"
        "  - id: S7\n    url: https://a.example.com\n    tier: T1\n    date: 2026-01-01\n"
        "  - url: https://b.example.com\n    tier: T2\n    date: 2026-01-02\n"
        "---\n\n"
        "## Alternativas evaluadas\nFoo.\n",
        encoding="utf-8",
    )

    changed = assign_source_ids(r)

    sources = parse_artifact(note).frontmatter["sources"]
    assert changed == 1
    assert [source["id"] for source in sources] == ["S7", "S8"]


def test_capture_declared_sources_generates_orgs_yaml(tmp_path):
    from sdr.snapshot import capture_declared_sources

    r = Research.create(base=tmp_path, slug="eval-foo", title="Evaluar Foo", question="¿Q?")
    note = r.root / "notes" / "n1.md"
    note.write_text(
        "---\n"
        "research: eval-foo\n"
        "date: 2026-07-03\n"
        "stage: explore\n"
        "sources:\n"
        "  - url: https://docs.foo.dev/guide\n    tier: T1\n    date: 2026-01-01\n"
        "  - url: https://github.com/bar/repo\n    tier: T1\n    date: 2026-01-01\n"
        "---\n\n"
        "## Alternativas evaluadas\nFoo.\n",
        encoding="utf-8",
    )

    def fetcher(url: str) -> FetchResult:
        return FetchResult(url=url, status_code=200, text="<html><body>Contenido.</body></html>")

    capture_declared_sources(r, fetcher=fetcher)

    orgs = (r.root / "notes" / "sources" / "orgs.yaml").read_text(encoding="utf-8")
    assert "sources:" in orgs
    assert "S1: foo" in orgs
    assert "S2: bar" in orgs
    assert "aliases:" in orgs


def test_capture_declared_sources_uses_existing_snapshot_cache(tmp_path):
    from sdr.snapshot import capture_declared_sources

    r = Research.create(base=tmp_path, slug="eval-foo", title="Evaluar Foo", question="¿Q?")
    note = r.root / "notes" / "n1.md"
    note.write_text(
        "---\n"
        "research: eval-foo\n"
        "date: 2026-07-03\n"
        "stage: explore\n"
        "sources:\n"
        "  - url: https://docs.foo.dev/guide\n    tier: T1\n    date: 2026-01-01\n"
        "---\n\n"
        "## Alternativas evaluadas\nFoo.\n",
        encoding="utf-8",
    )
    calls = 0

    def fetcher(url: str) -> FetchResult:
        nonlocal calls
        calls += 1
        return FetchResult(url=url, status_code=200, text="<html><body>Contenido.</body></html>")

    first = capture_declared_sources(r, fetcher=fetcher)
    second = capture_declared_sources(r, fetcher=fetcher)

    assert len(first) == 1
    assert second == []
    assert calls == 1
