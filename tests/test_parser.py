import textwrap

from sdr import parser


def _write(tmp_path, text):
    p = tmp_path / "artifact.md"
    p.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")
    return p


def test_parses_frontmatter_and_sections(tmp_path):
    path = _write(
        tmp_path,
        """
        ---
        research: eval-foo
        stage: intake
        ---

        ## Pregunta

        ¿Sirve foo para X?

        ## Hipótesis

        Creemos que sí.
        """,
    )
    art = parser.parse_artifact(path)
    assert art.frontmatter["research"] == "eval-foo"
    assert art.frontmatter["stage"] == "intake"
    assert "¿Sirve foo para X?" in art.section("Pregunta")
    assert "Creemos que sí." in art.section("Hipótesis")


def test_section_missing_returns_none(tmp_path):
    path = _write(tmp_path, "## Pregunta\n\ntexto\n")
    art = parser.parse_artifact(path)
    assert art.section("Alcance") is None


def test_empty_section_reports_no_content(tmp_path):
    path = _write(
        tmp_path,
        """
        ## Pregunta

        ## Hipótesis

        algo
        """,
    )
    art = parser.parse_artifact(path)
    assert not art.has_content("Pregunta")
    assert art.has_content("Hipótesis")


def test_section_match_allows_trailing_annotation(tmp_path):
    path = _write(
        tmp_path,
        """
        ## Criterios de evaluación (aceptación)

        - C1: latencia < 200ms
        """,
    )
    art = parser.parse_artifact(path)
    assert art.has_content("Criterios de evaluación")


def test_section_match_is_whitespace_and_case_insensitive(tmp_path):
    path = _write(tmp_path, "##   riesgos DE adopción\n\ntexto\n")
    art = parser.parse_artifact(path)
    assert art.has_content("Riesgos de adopción")
