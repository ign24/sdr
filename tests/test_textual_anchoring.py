import pytest

from sdr.textual_anchoring import (
    MATCHER_VERSION,
    NORMALIZATION_VERSION,
    TextLocator,
    TextMatch,
    match_text,
    normalize_text,
)


def test_versions_are_non_empty_strings():
    assert isinstance(NORMALIZATION_VERSION, str) and NORMALIZATION_VERSION
    assert isinstance(MATCHER_VERSION, str) and MATCHER_VERSION


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("  API\n\tESTABLE  ", "api estable"),
        ("Cafe\u0301", "café"),
        ("“rápido” — sí…", '"rápido" - sí...'),
        ("no supera 100 ms; x <= 3", "no supera 100 ms; x <= 3"),
    ],
)
def test_normalize_text_is_conservative(text, expected):
    assert normalize_text(text) == expected


def test_match_returns_literal_quote_and_inclusive_locator():
    snapshot = "Introducción.\nLa API es\nESTABLE para producción.\nCierre."

    result = match_text("la api es estable para producción.", snapshot)

    assert result == TextMatch(
        quote="La API es\nESTABLE para producción.",
        locator=TextLocator(line_start=2, line_end=3),
    )


def test_match_maps_unicode_and_typographic_punctuation_to_original_quote():
    snapshot = "Antes\nCafe\u0301 “premium” — cuesta 100\u00a0€.\nDespués"

    result = match_text('CAFÉ "premium" - cuesta 100 €.', snapshot)

    assert result == TextMatch(
        quote="Cafe\u0301 “premium” — cuesta 100\u00a0€.",
        locator=TextLocator(line_start=2, line_end=2),
    )


@pytest.mark.parametrize(
    ("claim", "snapshot"),
    [
        ("La API soporta modo offline.", "La API no soporta modo offline."),
        ("La latencia es 100 ms.", "La latencia es 200 ms."),
        ("El límite es 100 ms.", "El límite es 100 s."),
        ("La versión requiere x <= 3.", "La versión requiere x >= 3."),
        ("La versión requiere x < 3.", "La versión requiere x <= 3."),
    ],
)
def test_match_rejects_negation_magnitude_unit_and_operator_changes(claim, snapshot):
    assert match_text(claim, snapshot) is None


def test_match_chooses_first_literal_occurrence_stably():
    snapshot = "Objetivo en línea uno.\nOtra cosa.\nOBJETIVO EN LÍNEA UNO."

    result = match_text("objetivo en línea uno.", snapshot)

    assert result == TextMatch(
        quote="Objetivo en línea uno.",
        locator=TextLocator(line_start=1, line_end=1),
    )


@pytest.mark.parametrize("snapshot", ["", "   \n\t"])
def test_empty_or_whitespace_snapshot_has_no_match(snapshot):
    assert match_text("contenido", snapshot) is None


def test_empty_or_whitespace_claim_has_no_match():
    assert match_text(" \n", "contenido") is None


def test_match_is_exact_not_fuzzy():
    snapshot = "La plataforma ofrece almacenamiento local seguro y rápido."

    assert (
        match_text("La plataforma ofrece almacenamiento remoto seguro y rápido.", snapshot) is None
    )


def test_match_rejects_affirmative_claim_immediately_prefixed_by_negation():
    assert (
        match_text("La API soporta modo offline.", "La guía dice: no La API soporta modo offline.")
        is None
    )


@pytest.mark.parametrize(
    ("claim", "snapshot"),
    [
        ("100 ms", "La latencia es 1100 ms."),
        ("ms", "La distancia se expresa en kms."),
        ("2", "El valor es ²."),
        ("iv", "Capítulo Ⅳ."),
        ("s", "La letra es ß."),
    ],
)
def test_match_rejects_partial_words_and_compatibility_expansions(claim, snapshot):
    assert match_text(claim, snapshot) is None


def test_normalization_preserves_compatibility_characters():
    assert normalize_text("2 ² iv Ⅳ s ß") == "2 ² iv ⅳ s ß"


def test_partial_ellipsis_expansion_is_skipped_for_next_valid_match():
    result = match_text(".", "Primero…\nLuego.")

    assert result == TextMatch(quote=".", locator=TextLocator(line_start=2, line_end=2))


def test_full_ellipsis_equivalence_remains_matchable():
    result = match_text("espera...", "Espera… y continúa.")

    assert result == TextMatch(quote="Espera…", locator=TextLocator(line_start=1, line_end=1))


@pytest.mark.parametrize(
    ("claim", "snapshot"),
    [
        ("s", "ß"),
        (".", "…"),
    ],
)
def test_match_never_returns_a_quote_with_different_normalized_text(claim, snapshot):
    result = match_text(claim, snapshot)

    assert result is None or normalize_text(result.quote) == normalize_text(claim)


@pytest.mark.parametrize(
    ("claim", "snapshot"),
    [
        ("가", "가"),
        ("가", "가"),
        ("각", "각"),
        ("각", "각"),
    ],
)
def test_match_supports_canonically_equivalent_hangul_in_both_directions(claim, snapshot):
    result = match_text(claim, snapshot)

    assert result == TextMatch(quote=snapshot, locator=TextLocator(line_start=1, line_end=1))
    assert normalize_text(result.quote) == normalize_text(claim)
