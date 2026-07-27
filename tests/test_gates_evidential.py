import textwrap

from sdr import gates, probe_verify
from sdr.research import Research


def _make(tmp_path, mode="full"):
    return Research.create(
        base=tmp_path, slug="eval-foo", title="Evaluar Foo", question="¿Q?", mode=mode
    )


def _note(sources_yaml: str, body: str = "") -> str:
    default_body = textwrap.dedent(
        """
        ## Alternativas evaluadas
        Foo vs Bar [S1].

        ## Madurez
        Estable [S1].

        ## Costos
        Bajo [S2].

        ## Riesgos
        Lock-in.

        ## Contra-evidencia
        No se encontraron señales contrarias tras buscar benchmarks negativos.
        """
    ).strip()
    return (
        "---\n"
        "research: eval-foo\n"
        "date: 2026-07-03\n"
        "stage: explore\n"
        f"sources:\n{sources_yaml}"
        "---\n\n"
        f"{body or default_body}\n"
    )


# --- explore: tiers y triangulación ---------------------------------------


def _ok_sources() -> str:
    return (
        "  - id: S1\n    url: https://docs.foo.dev/guide\n    tier: T1\n    date: 2026-01-01\n"
        "  - id: S2\n    url: https://bench.example.com/x\n    tier: T2\n    date: 2026-02-01\n"
    )


def test_explore_passes_with_t1_and_two_domains(tmp_path):
    r = _make(tmp_path)
    (r.root / "notes" / "n1.md").write_text(_note(_ok_sources()), encoding="utf-8")
    report = gates.check_stage(r, stage="explore", offline=True)
    assert report.passed, report.failures


def test_explore_fails_when_source_date_is_missing(tmp_path):
    r = _make(tmp_path)
    sources = (
        "  - url: https://docs.foo.dev/guide\n    tier: T1\n"
        "  - url: https://bench.example.com/x\n    tier: T2\n    date: 2026-02-01\n"
    )
    (r.root / "notes" / "n1.md").write_text(_note(sources), encoding="utf-8")
    report = gates.check_stage(r, stage="explore", offline=True)
    assert not report.passed
    assert any(f.check == "source_dates" and "docs.foo.dev" in f.detail for f in report.failures)


def test_explore_v2_fails_without_counter_evidence(tmp_path):
    r = _make(tmp_path)
    body = textwrap.dedent(
        """
        ## Alternativas evaluadas
        Foo vs Bar.

        ## Madurez
        Estable.

        ## Costos
        Bajo.

        ## Riesgos
        Lock-in.
        """
    ).strip()
    (r.root / "notes" / "n1.md").write_text(_note(_ok_sources(), body=body), encoding="utf-8")
    report = gates.check_stage(r, stage="explore", offline=True)
    assert any("Contra-evidencia" in f.detail for f in report.failures)


def test_explore_v1_does_not_require_counter_evidence(tmp_path):
    r = _make(tmp_path)
    r.meta.schema_version = 1
    body = textwrap.dedent(
        """
        ## Alternativas evaluadas
        Foo vs Bar.

        ## Madurez
        Estable.

        ## Costos
        Bajo.

        ## Riesgos
        Lock-in.
        """
    ).strip()
    (r.root / "notes" / "n1.md").write_text(_note(_ok_sources(), body=body), encoding="utf-8")
    report = gates.check_stage(r, stage="explore", offline=True)
    assert not any("Contra-evidencia" in f.detail for f in report.failures)


def test_claim_citation_coverage_fails_unknown_source_marker(tmp_path):
    r = _make(tmp_path)
    sources = (
        "  - id: S1\n    url: https://docs.foo.dev/guide\n    tier: T1\n    date: 2026-01-01\n"
        "  - id: S2\n    url: https://bench.example.com/x\n    tier: T2\n    date: 2026-02-01\n"
    )
    body = textwrap.dedent(
        """
        ## Alternativas evaluadas
        Foo tiene soporte estable [S9].

        ## Madurez
        Estable [S1].

        ## Costos
        Bajo [S2].

        ## Riesgos
        Lock-in [S1].

        ## Contra-evidencia
        No se encontraron señales contrarias [S2].
        """
    ).strip()
    (r.root / "notes" / "n1.md").write_text(_note(sources, body=body), encoding="utf-8")
    report = gates.check_stage(r, stage="explore", offline=True)
    assert any(f.check == "claim_citation_coverage" and "S9" in f.detail for f in report.failures)


def test_claim_citation_coverage_fails_unknown_source_marker_in_heading(tmp_path):
    r = _make(tmp_path)
    body = textwrap.dedent(
        """
        ## Alternativas evaluadas [S9]
        Foo tiene soporte estable [S1].

        ## Madurez
        Estable [S1].

        ## Costos
        Bajo [S2].

        ## Riesgos
        Lock-in [S1].

        ## Contra-evidencia
        No se encontraron señales contrarias [cf.S2].
        """
    ).strip()
    (r.root / "notes" / "n1.md").write_text(_note(_ok_sources(), body=body), encoding="utf-8")

    report = gates.check_stage(r, stage="explore", offline=True)

    assert any(
        failure.check == "claim_citation_coverage"
        and "[S9]" in failure.detail
        and "S9" in failure.detail
        for failure in report.failures
    )


def test_claim_citation_coverage_fails_unknown_contextual_source_marker(tmp_path):
    r = _make(tmp_path)
    body = textwrap.dedent(
        """
        ## Alternativas evaluadas
        Foo tiene soporte estable [cf. S9].

        ## Madurez
        Estable [cf. S1].

        ## Costos
        Bajo [cf. S2].

        ## Riesgos
        Lock-in.

        ## Contra-evidencia
        No se encontraron señales contrarias [cf. S2].
        """
    ).strip()
    (r.root / "notes" / "n1.md").write_text(_note(_ok_sources(), body=body), encoding="utf-8")

    report = gates.check_stage(r, stage="explore", offline=True)

    assert any(
        f.check == "claim_citation_coverage"
        and "n1.md" in f.detail
        and "[cf. S9]" in f.detail
        and "S9" in f.detail
        for f in report.failures
    )


def test_claim_citation_coverage_allows_contextual_only_note(tmp_path):
    r = _make(tmp_path)
    body = textwrap.dedent(
        """
        ## Alternativas evaluadas
        Foo se compara con Bar [cf. S1].

        ## Madurez
        El contexto de adopción es estable [cf. S1].

        ## Costos
        El análisis de costos es favorable [cf. S2].

        ## Riesgos
        Lock-in [cf. S1].

        ## Contra-evidencia
        Se revisó evidencia contraria [cf. S2].
        """
    ).strip()
    (r.root / "notes" / "n1.md").write_text(_note(_ok_sources(), body=body), encoding="utf-8")

    report = gates.check_stage(r, stage="explore", offline=True)

    assert all(
        result.passed for result in report.results if result.check == "claim_citation_coverage"
    )


def test_claim_citation_coverage_allows_one_factual_with_contextual_references(tmp_path):
    r = _make(tmp_path)
    body = textwrap.dedent(
        """
        ## Alternativas evaluadas
        Foo reduce latencia [S1] en el contexto comparado [cf. S2].

        ## Madurez
        Estable [S1].

        ## Costos
        Bajo [S2].

        ## Riesgos
        Lock-in.

        ## Contra-evidencia
        Se revisó evidencia contraria [cf. S2].
        """
    ).strip()
    (r.root / "notes" / "n1.md").write_text(_note(_ok_sources(), body=body), encoding="utf-8")

    report = gates.check_stage(r, stage="explore", offline=True)

    assert all(
        result.passed for result in report.results if result.check == "claim_citation_coverage"
    )


def test_claim_citation_coverage_rejects_multiple_factual_markers_actionably(tmp_path):
    r = _make(tmp_path)
    body = textwrap.dedent(
        """
        ## Alternativas evaluadas
        Foo reduce latencia [S1] y costo [S2].

        ## Madurez
        Estable [S1].

        ## Costos
        Bajo [S2].

        ## Riesgos
        Lock-in.

        ## Contra-evidencia
        Se revisó evidencia contraria [cf. S2].
        """
    ).strip()
    (r.root / "notes" / "n1.md").write_text(_note(_ok_sources(), body=body), encoding="utf-8")

    report = gates.check_stage(r, stage="explore", offline=True)

    failure = next(
        result
        for result in report.failures
        if result.check == "claim_citation_coverage" and "divida la oración" in result.detail
    )
    assert "n1.md" in failure.detail
    assert "línea" in failure.detail
    assert "[S1]" in failure.detail and "[S2]" in failure.detail


def test_claim_citation_coverage_rejects_multiline_sentence_with_two_factual_markers(tmp_path):
    r = _make(tmp_path)
    body = textwrap.dedent(
        """
        ## Alternativas evaluadas
        Foo reduce latencia [S1]
        y también reduce costo [S2].

        ## Madurez
        Estable [S1].

        ## Costos
        Bajo [S2].

        ## Riesgos
        Lock-in.

        ## Contra-evidencia
        Se revisó evidencia contraria [cf. S2].
        """
    ).strip()
    (r.root / "notes" / "n1.md").write_text(_note(_ok_sources(), body=body), encoding="utf-8")

    report = gates.check_stage(r, stage="explore", offline=True)

    failure = next(
        result
        for result in report.failures
        if result.check == "claim_citation_coverage" and "divida la oración" in result.detail
    )
    assert "líneas" in failure.detail
    assert "[S1]" in failure.detail and "[S2]" in failure.detail


def test_claim_citation_coverage_uses_same_contextual_variants_as_claim_parser(tmp_path):
    r = _make(tmp_path)
    body = textwrap.dedent(
        """
        ## Alternativas evaluadas
        Foo se compara con Bar [CF.s1].

        ## Madurez
        El contexto es estable [cf.   S1].

        ## Costos
        El análisis es favorable [cF   .   s2].

        ## Riesgos
        Lock-in.

        ## Contra-evidencia
        Se revisó evidencia contraria [cf.S2].
        """
    ).strip()
    (r.root / "notes" / "n1.md").write_text(_note(_ok_sources(), body=body), encoding="utf-8")

    report = gates.check_stage(r, stage="explore", offline=True)

    assert all(
        result.passed for result in report.results if result.check == "claim_citation_coverage"
    )


def test_claim_citation_coverage_ignores_markers_in_frontmatter_and_code(tmp_path):
    r = _make(tmp_path)
    body = textwrap.dedent(
        """
        ## Alternativas evaluadas
        Foo se compara con Bar [cf. S1] y muestra `[S8]` como ejemplo.

        ```markdown
        Referencia de ejemplo [S9].
        ```

        ## Madurez
        Estable [S1].

        ## Costos
        Bajo [S2].

        ## Riesgos
        Lock-in.

        ## Contra-evidencia
        Se revisó evidencia contraria [cf. S2].
        """
    ).strip()
    note = _note(_ok_sources(), body=body).replace(
        "stage: explore\n", 'stage: explore\nexample: "[S7]"\n'
    )
    (r.root / "notes" / "n1.md").write_text(note, encoding="utf-8")

    report = gates.check_stage(r, stage="explore", offline=True)

    assert not any(
        result.check == "claim_citation_coverage"
        and any(marker in result.detail for marker in ("S7", "S8", "S9"))
        for result in report.failures
    )


def test_claim_citation_coverage_ignores_indented_code_and_url_destinations(tmp_path):
    r = _make(tmp_path)
    body = textwrap.dedent(
        """
        ## Alternativas evaluadas
        [Foo es estable [S1]](https://example.com/[S9]).

            Ejemplo de código [S8].

        ## Madurez
        Estable [S1].

        ## Costos
        Bajo [S2].

        ## Riesgos
        <https://example.com/[S7]>

        ## Contra-evidencia
        Se revisó evidencia contraria [cf. S2].
        """
    ).strip()
    (r.root / "notes" / "n1.md").write_text(_note(_ok_sources(), body=body), encoding="utf-8")

    report = gates.check_stage(r, stage="explore", offline=True)

    assert not any(
        result.check == "claim_citation_coverage"
        and any(marker in result.detail for marker in ("S7", "S8", "S9"))
        for result in report.failures
    )


def test_claim_citation_coverage_requires_citations_in_key_sections(tmp_path):
    r = _make(tmp_path)
    body = textwrap.dedent(
        """
        ## Alternativas evaluadas
        Foo vs Bar.

        ## Madurez
        Estable.

        ## Costos
        Bajo.

        ## Riesgos
        Lock-in [S1].

        ## Contra-evidencia
        No se encontraron señales contrarias [S2].
        """
    ).strip()
    (r.root / "notes" / "n1.md").write_text(_note(_ok_sources(), body=body), encoding="utf-8")
    report = gates.check_stage(r, stage="explore", offline=True)
    assert any(
        f.check == "claim_citation_coverage" and "Alternativas evaluadas" in f.detail
        for f in report.failures
    )
    assert any(
        f.check == "claim_citation_coverage" and "Madurez" in f.detail for f in report.failures
    )
    assert any(
        f.check == "claim_citation_coverage" and "Costos" in f.detail for f in report.failures
    )


def test_claim_citation_coverage_is_not_required_in_schema_v1(tmp_path):
    r = _make(tmp_path)
    r.meta.schema_version = 1
    body = textwrap.dedent(
        """
        ## Alternativas evaluadas
        Foo vs Bar.

        ## Madurez
        Estable.

        ## Costos
        Bajo.

        ## Riesgos
        Lock-in.
        """
    ).strip()
    (r.root / "notes" / "n1.md").write_text(_note(_ok_sources(), body=body), encoding="utf-8")
    report = gates.check_stage(r, stage="explore", offline=True)
    assert not any(result.check == "claim_citation_coverage" for result in report.results)


def test_explore_passes_when_all_source_dates_are_present(tmp_path):
    r = _make(tmp_path)
    (r.root / "notes" / "n1.md").write_text(_note(_ok_sources()), encoding="utf-8")
    report = gates.check_stage(r, stage="explore", offline=True)
    assert all(x.passed for x in report.results if x.check == "source_dates")


def test_tier_plausibility_fails_inflated_tier_without_justification(tmp_path):
    r = _make(tmp_path)
    sources = (
        "  - id: S1\n    url: https://random-blog.example/post\n    tier: T1\n    date: 2026-01-01\n"
        "  - id: S2\n    url: https://bench.example.com/x\n    tier: T2\n    date: 2026-02-01\n"
    )
    (r.root / "notes" / "n1.md").write_text(_note(sources), encoding="utf-8")

    report = gates.check_stage(r, stage="explore", offline=True)

    assert any(f.check == "tier_plausibility" and "T3" in f.detail for f in report.failures)


def test_tier_plausibility_allows_justification(tmp_path):
    r = _make(tmp_path)
    sources = (
        "  - id: S1\n    url: https://random-blog.example/post\n    tier: T1\n    tier_justification: autor mantiene el benchmark oficial\n    date: 2026-01-01\n"
        "  - id: S2\n    url: https://bench.example.com/x\n    tier: T2\n    date: 2026-02-01\n"
    )
    (r.root / "notes" / "n1.md").write_text(_note(sources), encoding="utf-8")

    report = gates.check_stage(r, stage="explore", offline=True)

    assert not any(f.check == "tier_plausibility" and not f.passed for f in report.results)


def test_source_dates_fails_when_source_is_stale_without_justification(tmp_path):
    r = _make(tmp_path)
    r.artifact_path("brief.md").write_text("---\ndate: 2026-07-03\n---\n", encoding="utf-8")
    sources = (
        "  - id: S1\n    url: https://docs.foo.dev/guide\n    tier: T1\n    date: 2020-01-01\n"
        "  - id: S2\n    url: https://bench.example.com/x\n    tier: T2\n    date: 2026-02-01\n"
    )
    (r.root / "notes" / "n1.md").write_text(_note(sources), encoding="utf-8")

    report = gates.check_stage(r, stage="explore", offline=True)

    assert any(f.check == "source_dates" and "vencida" in f.detail for f in report.failures)


def test_source_dates_allows_date_justification(tmp_path):
    r = _make(tmp_path)
    r.artifact_path("brief.md").write_text("---\ndate: 2026-07-03\n---\n", encoding="utf-8")
    sources = (
        "  - id: S1\n    url: https://docs.foo.dev/guide\n    tier: T1\n    date: 2020-01-01\n    date_justification: documento fundacional estable\n"
        "  - id: S2\n    url: https://bench.example.com/x\n    tier: T2\n    date: 2026-02-01\n"
    )
    (r.root / "notes" / "n1.md").write_text(_note(sources), encoding="utf-8")

    report = gates.check_stage(r, stage="explore", offline=True)

    assert not any(f.check == "source_dates" and "vencida" in f.detail for f in report.failures)


def test_explore_fails_without_t1_source(tmp_path):
    r = _make(tmp_path)
    sources = (
        "  - url: https://blog.a.com/x\n    tier: T3\n    date: 2026-01-01\n"
        "  - url: https://blog.b.com/y\n    tier: T3\n    date: 2026-01-01\n"
    )
    (r.root / "notes" / "n1.md").write_text(_note(sources), encoding="utf-8")
    report = gates.check_stage(r, stage="explore", offline=True)
    assert not report.passed
    assert any(f.check == "source_tiers" for f in report.failures)


def test_explore_fails_with_single_domain(tmp_path):
    r = _make(tmp_path)
    sources = (
        "  - url: https://docs.foo.dev/a\n    tier: T1\n    date: 2026-01-01\n"
        "  - url: https://docs.foo.dev/b\n    tier: T2\n    date: 2026-01-01\n"
    )
    (r.root / "notes" / "n1.md").write_text(_note(sources), encoding="utf-8")
    report = gates.check_stage(r, stage="explore", offline=True)
    assert not report.passed
    assert any(f.check == "source_triangulation" for f in report.failures)


def test_www_prefix_does_not_count_as_distinct_domain(tmp_path):
    r = _make(tmp_path)
    sources = (
        "  - url: https://www.foo.dev/a\n    tier: T1\n    date: 2026-01-01\n"
        "  - url: https://foo.dev/b\n    tier: T2\n    date: 2026-01-01\n"
    )
    (r.root / "notes" / "n1.md").write_text(_note(sources), encoding="utf-8")
    report = gates.check_stage(r, stage="explore", offline=True)
    assert any(f.check == "source_triangulation" for f in report.failures)


def test_github_repos_from_same_owner_count_as_one_org(tmp_path):
    r = _make(tmp_path)
    sources = (
        "  - url: https://github.com/acme/repo-a\n    tier: T1\n    date: 2026-01-01\n"
        "  - url: https://github.com/acme/repo-b\n    tier: T2\n    date: 2026-01-01\n"
    )
    (r.root / "notes" / "n1.md").write_text(_note(sources), encoding="utf-8")
    report = gates.check_stage(r, stage="explore", offline=True)
    assert any(
        f.check == "source_triangulation" and "organizaciones" in f.detail for f in report.failures
    )


def test_vendor_mirrors_count_as_one_org(tmp_path):
    r = _make(tmp_path)
    sources = (
        "  - url: https://docs.vendor.com/a\n    tier: T1\n    date: 2026-01-01\n"
        "  - url: https://vendor.com/b\n    tier: T2\n    date: 2026-01-01\n"
        "  - url: https://github.com/vendor/repo\n    tier: T1\n    date: 2026-01-01\n"
    )
    (r.root / "notes" / "n1.md").write_text(_note(sources), encoding="utf-8")
    report = gates.check_stage(r, stage="explore", offline=True)
    assert any(
        f.check == "source_triangulation" and "organizaciones" in f.detail for f in report.failures
    )


def test_org_aliases_yaml_collapses_sources(tmp_path):
    r = _make(tmp_path)
    sources = (
        "  - url: https://docs.foo.dev/a\n    tier: T1\n    date: 2026-01-01\n"
        "  - url: https://bench.example.com/x\n    tier: T2\n    date: 2026-02-01\n"
    )
    (r.root / "notes" / "n1.md").write_text(_note(sources), encoding="utf-8")
    sources_dir = r.root / "notes" / "sources"
    sources_dir.mkdir()
    (sources_dir / "orgs.yaml").write_text(
        "aliases:\n  foo: vendor\n  bench: vendor\n",
        encoding="utf-8",
    )
    report = gates.check_stage(r, stage="explore", offline=True)
    assert any(f.check == "source_triangulation" for f in report.failures)


def test_per_alternative_t1_requirement(tmp_path):
    r = _make(tmp_path)
    sources = (
        "  - url: https://docs.foo.dev/a\n    tier: T1\n    date: 2026-01-01\n    alternative: foo\n"
        "  - url: https://blog.bar.io/b\n    tier: T3\n    date: 2026-01-01\n    alternative: bar\n"
    )
    (r.root / "notes" / "n1.md").write_text(_note(sources), encoding="utf-8")
    report = gates.check_stage(r, stage="explore", offline=True)
    assert not report.passed
    assert any("bar" in f.detail for f in report.failures)


def test_per_alternative_triangulation_requirement(tmp_path):
    r = _make(tmp_path)
    sources = (
        "  - url: https://docs.foo.dev/a\n    tier: T1\n    date: 2026-01-01\n    alternative: foo\n"
        "  - url: https://bench.foo.org/a\n    tier: T2\n    date: 2026-01-02\n    alternative: foo\n"
        "  - url: https://docs.bar.dev/b\n    tier: T1\n    date: 2026-01-01\n    alternative: bar\n"
        "  - url: https://docs.bar.dev/c\n    tier: T2\n    date: 2026-01-02\n    alternative: bar\n"
    )
    (r.root / "notes" / "n1.md").write_text(_note(sources), encoding="utf-8")
    report = gates.check_stage(r, stage="explore", offline=True)
    assert not report.passed
    assert any(f.check == "source_triangulation" and "bar" in f.detail for f in report.failures)


def test_per_alternative_triangulation_passes_with_two_domains_each(tmp_path):
    r = _make(tmp_path)
    sources = (
        "  - url: https://docs.foo.dev/a\n    tier: T1\n    date: 2026-01-01\n    alternative: foo\n"
        "  - url: https://bench.example.com/a\n    tier: T2\n    date: 2026-01-02\n    alternative: foo\n"
        "  - url: https://docs.bar.dev/b\n    tier: T1\n    date: 2026-01-01\n    alternative: bar\n"
        "  - url: https://bench.example.org/b\n    tier: T2\n    date: 2026-01-02\n    alternative: bar\n"
    )
    (r.root / "notes" / "n1.md").write_text(_note(sources), encoding="utf-8")
    report = gates.check_stage(r, stage="explore", offline=True)
    assert all(x.passed for x in report.results if x.check == "source_triangulation")


def test_links_offline_is_skipped_not_passed(tmp_path):
    r = _make(tmp_path)
    (r.root / "notes" / "n1.md").write_text(_note(_ok_sources()), encoding="utf-8")
    report = gates.check_stage(r, stage="explore", offline=True)
    link_results = [x for x in report.results if x.check == "links_resolve"]
    assert link_results
    assert link_results[0].passed is False
    assert link_results[0].skipped is True
    assert report.passed is True
    assert link_results[0] not in report.failures


def test_links_broken_fails_when_online(tmp_path):
    r = _make(tmp_path)
    (r.root / "notes" / "n1.md").write_text(_note(_ok_sources()), encoding="utf-8")
    report = gates.check_stage(
        r, stage="explore", offline=False, url_checker=lambda u: "bench" not in u
    )
    assert not report.passed
    assert any(f.check == "links_resolve" and "bench" in f.detail for f in report.failures)


# --- probe: cross-reference y reproducibilidad -----------------------------


def _brief_with_criteria(r, ids):
    lines = "\n".join(f"- {i}: criterio" for i in ids)
    template = textwrap.dedent(
        """
        ---
        research: eval-foo
        date: 2026-07-03
        stage: intake
        owner: nacho
        timebox: 3
        ---

        ## Criterios de evaluación
        __CRITERIA__
        """
    ).lstrip()
    r.artifact_path("brief.md").write_text(
        template.replace("__CRITERIA__", lines), encoding="utf-8"
    )


def test_probe_fails_when_a_criterion_has_no_result(tmp_path):
    r = _make(tmp_path)
    _brief_with_criteria(r, ["C1", "C2", "C3"])
    results = (
        "---\nresearch: eval-foo\ndate: 2026-07-03\nstage: probe\nverify:\n  action: run\n  command: python bench.py\n  expect: OK\n---\n\n"
        "## Resultados por criterio\nC1 cumple. C2 parcial.\n\n"
        "## Reproducción\n```bash\npython bench.py\n```\n"
    )
    r.artifact_path("probe/results.md").write_text(results, encoding="utf-8")
    report = gates.check_stage(r, stage="probe")
    assert not report.passed
    assert any(f.check == "criteria_cross_reference" and "C3" in f.detail for f in report.failures)


def test_probe_passes_with_all_criteria_and_repro(tmp_path):
    r = _make(tmp_path)
    _brief_with_criteria(r, ["C1", "C2"])
    results = (
        "---\nresearch: eval-foo\ndate: 2026-07-03\nstage: probe\nverify:\n  action: run\n  command: python bench.py\n  expect: OK\n---\n\n"
        "## Resultados por criterio\nC1 cumple, C2 no cumple.\n\n"
        "## Reproducción\n```bash\npython bench.py\n```\n"
    )
    r.artifact_path("probe/results.md").write_text(results, encoding="utf-8")
    report = gates.check_stage(r, stage="probe")
    assert report.passed, report.failures


def test_probe_fails_when_referenced_artifact_is_missing(tmp_path):
    r = _make(tmp_path)
    _brief_with_criteria(r, ["C1", "C2"])
    results = (
        "---\nresearch: eval-foo\ndate: 2026-07-03\nstage: probe\nverify:\n  action: run\n  command: python bench.py\n  expect: OK\n---\n\n"
        "## Resultados por criterio\nC1 cumple, C2 no cumple. Evidencia: [salida](probe/output.json).\n\n"
        "## Reproducción\n```bash\npython bench.py > probe/output.json\n```\n"
    )
    r.artifact_path("probe/results.md").write_text(results, encoding="utf-8")
    report = gates.check_stage(r, stage="probe")
    assert not report.passed
    assert any(
        f.check == "probe_artifacts_exist" and "probe/output.json" in f.detail
        for f in report.failures
    )


def test_probe_passes_when_referenced_artifact_exists(tmp_path):
    r = _make(tmp_path)
    _brief_with_criteria(r, ["C1", "C2"])
    r.artifact_path("probe/output.json").write_text('{"ok": true}', encoding="utf-8")
    results = (
        "---\nresearch: eval-foo\ndate: 2026-07-03\nstage: probe\nverify:\n  action: run\n  command: python bench.py\n  expect: OK\n---\n\n"
        "## Resultados por criterio\nC1 cumple, C2 no cumple. Evidencia: `probe/output.json`.\n\n"
        "## Reproducción\n```bash\npython bench.py > probe/output.json\n```\n"
    )
    r.artifact_path("probe/results.md").write_text(results, encoding="utf-8")
    report = gates.check_stage(r, stage="probe")
    assert all(x.passed for x in report.results if x.check == "probe_artifacts_exist")


def test_probe_fails_without_reproducible_block(tmp_path):
    r = _make(tmp_path)
    _brief_with_criteria(r, ["C1", "C2"])
    results = (
        "---\nresearch: eval-foo\ndate: 2026-07-03\nstage: probe\nverify:\n  action: run\n  command: python bench.py\n  expect: OK\n---\n\n"
        "## Resultados por criterio\nC1 cumple, C2 no cumple.\n\n"
        "## Reproducción\nCorrer el script manualmente.\n"
    )
    r.artifact_path("probe/results.md").write_text(results, encoding="utf-8")
    report = gates.check_stage(r, stage="probe")
    assert not report.passed
    assert any(f.check == "benchmark_reproducible" for f in report.failures)


def test_probe_fails_with_benchmark_table_without_repro_command(tmp_path):
    r = _make(tmp_path)
    _brief_with_criteria(r, ["C1", "C2"])
    results = (
        "---\nresearch: eval-foo\ndate: 2026-07-03\nstage: probe\nverify:\n  action: run\n  command: python bench.py\n  expect: OK\n---\n\n"
        "## Resultados por criterio\n"
        "| criterio | resultado |\n|---|---|\n| C1 | 120ms |\n| C2 | 8 USD |\n\n"
        "## Reproducción\nLos resultados salen de una corrida local documentada.\n"
    )
    r.artifact_path("probe/results.md").write_text(results, encoding="utf-8")
    report = gates.check_stage(r, stage="probe")
    assert not report.passed
    assert any(f.check == "benchmark_reproducible" for f in report.failures)


def test_probe_passes_with_benchmark_table_and_repro_command(tmp_path):
    r = _make(tmp_path)
    _brief_with_criteria(r, ["C1", "C2"])
    results = (
        "---\nresearch: eval-foo\ndate: 2026-07-03\nstage: probe\nverify:\n  action: run\n  command: python bench.py\n  expect: OK\n---\n\n"
        "## Resultados por criterio\n"
        "| criterio | resultado |\n|---|---|\n| C1 | 120ms |\n| C2 | 8 USD |\n\n"
        "## Reproducción\n```bash\npython bench.py --json\n```\n"
    )
    r.artifact_path("probe/results.md").write_text(results, encoding="utf-8")
    report = gates.check_stage(r, stage="probe")
    assert all(x.passed for x in report.results if x.check == "benchmark_reproducible")


# --- transfer: y-statement y ring acoplado a evidencia ---------------------


def _memo(ring: str, recommendation: str) -> str:
    return textwrap.dedent(
        f"""
        ---
        research: eval-foo
        date: 2026-07-03
        stage: transfer
        ring: {ring}
        audience: equipo
        ---

        ## Recomendación
        {recommendation}

        ## Alternativas evaluadas
        Foo, Bar.

        ## Criterios de selección
        Costo y madurez.

        ## Riesgos y limitaciones
        Lock-in.

        ## Próximos pasos
        Piloto.

        ## Audiencia
        Equipo técnico.
        """
    ).lstrip()


def _complete_recommendation() -> str:
    return (
        "Decidimos evaluar Foo para soporte técnico, porque la evidencia de C1 y C2 "
        "muestra ajuste parcial, aceptando el trade-off de no adoptarlo todavía."
    )


def test_transfer_light_mode_rejects_adopt_ring(tmp_path):
    r = _make(tmp_path, mode="light")
    r.artifact_path("decision-memo.md").write_text(
        _memo("adopt", _complete_recommendation()), encoding="utf-8"
    )
    report = gates.check_stage(r, stage="transfer")
    assert not report.passed
    assert any(f.check == "ring_backed_by_evidence" for f in report.failures)


def test_transfer_adopt_requires_probe_validated(tmp_path):
    r = _make(tmp_path, mode="full")
    r.artifact_path("decision-memo.md").write_text(
        _memo("adopt", _complete_recommendation()), encoding="utf-8"
    )
    report = gates.check_stage(r, stage="transfer")
    assert any(f.check == "ring_backed_by_evidence" for f in report.failures)
    # Con probe validado y verify-probe vigente, el mismo memo pasa el check de ring.
    r.artifact_path("probe/results.md").write_text("ok", encoding="utf-8")
    r.meta.validation["probe"] = "deadbeef"
    r.meta.verify_probe = {"result": "pass", "probe_hash": probe_verify.hash_probe_dir(r)}
    r.save()
    report2 = gates.check_stage(r, stage="transfer")
    assert all(x.passed for x in report2.results if x.check == "ring_backed_by_evidence")


def test_transfer_fails_without_y_statement(tmp_path):
    r = _make(tmp_path, mode="light")
    r.artifact_path("decision-memo.md").write_text(
        _memo("assess", "Recomendamos usar Foo."), encoding="utf-8"
    )
    report = gates.check_stage(r, stage="transfer")
    assert not report.passed
    assert any(f.check == "y_statement" for f in report.failures)


def test_transfer_keyword_only_y_statement_fails(tmp_path):
    r = _make(tmp_path, mode="light")
    r.artifact_path("decision-memo.md").write_text(
        _memo("assess", "En el contexto de X decidimos Y aceptando Z."), encoding="utf-8"
    )
    report = gates.check_stage(r, stage="transfer")
    assert not report.passed
    assert any(f.check == "y_statement" for f in report.failures)


def test_transfer_complete_y_statement_passes(tmp_path):
    r = _make(tmp_path, mode="light")
    r.artifact_path("decision-memo.md").write_text(
        _memo("assess", _complete_recommendation()), encoding="utf-8"
    )
    report = gates.check_stage(r, stage="transfer")
    assert all(x.passed for x in report.results if x.check == "y_statement")


# --- reuse: metadata de asset ---------------------------------------------


def test_reuse_requires_type_and_audience(tmp_path):
    r = _make(tmp_path)
    (r.root / "assets" / "post.md").write_text(
        "---\nresearch: eval-foo\ndate: 2026-07-03\nstage: reuse\naudience: externa\n---\n\ncontenido\n",
        encoding="utf-8",
    )
    report = gates.check_stage(r, stage="reuse")
    assert not report.passed
    assert any(f.check == "asset_metadata" and "type" in f.detail for f in report.failures)


def test_reuse_passes_with_full_metadata(tmp_path):
    r = _make(tmp_path)
    (r.root / "assets" / "post.md").write_text(
        "---\nresearch: eval-foo\ndate: 2026-07-03\nstage: reuse\ntype: post\naudience: external\n---\n\ncontenido\n",
        encoding="utf-8",
    )
    report = gates.check_stage(r, stage="reuse")
    assert report.passed, report.failures


def test_reuse_rejects_non_public_asset_vocabulary(tmp_path):
    r = _make(tmp_path)
    (r.root / "assets" / "post.md").write_text(
        "---\nresearch: eval-foo\ndate: 2026-07-03\nstage: reuse\n"
        "type: carrusel\naudience: externa\n---\n\ncontenido\n",
        encoding="utf-8",
    )

    report = gates.check_stage(r, stage="reuse")

    assert not report.passed
    assert {failure.check for failure in report.failures} == {"asset_metadata"}
    assert any(
        "type" in failure.detail and "carrusel" in failure.detail for failure in report.failures
    )
    assert any(
        "audience" in failure.detail and "externa" in failure.detail for failure in report.failures
    )
