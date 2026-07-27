"""Modelo de una investigación y su estado persistido en `sdr.yaml`."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from sdr import schema
from sdr.paths import (
    ensure_tree_within,
    ensure_within,
    resolve_child,
    resolve_root,
    resolve_segment,
)

_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

META_FILE = "sdr.yaml"
_STAGE_DIRS = ("notes", "probe", "assets")


def is_valid_slug(slug: str) -> bool:
    """True si `slug` es kebab-case válido."""
    return bool(_SLUG_RE.match(slug))


class Approval(BaseModel):
    """Aprobación humana del decision memo (etapa transfer)."""

    model_config = ConfigDict(extra="allow")

    by: str
    date: str


class Reopen(BaseModel):
    """Registro de un retroceso de etapa (backtracking explícito)."""

    model_config = ConfigDict(extra="allow")

    from_stage: str
    to_stage: str
    reason: str
    date: str


class ResearchMeta(BaseModel):
    """Metadata de una investigación (contenido de `sdr.yaml`)."""

    model_config = ConfigDict(extra="allow")

    slug: str
    title: str
    question: str
    mode: str = "full"
    stage: str = "intake"
    status: str = "active"  # active | done | dropped
    owner: str = ""
    timebox: int = 0  # estimación en días
    created: str = Field(default_factory=lambda: date.today().isoformat())
    updated: str = Field(default_factory=lambda: date.today().isoformat())
    tags: list[str] = Field(default_factory=list)
    schema_version: int = 1
    dropped_reason: str = ""
    validation: dict[str, str] = Field(default_factory=dict)  # stage -> hash del gate
    judge: dict[str, Any] = Field(default_factory=dict)
    verify_probe: dict[str, Any] = Field(default_factory=dict)
    overrides: list[dict[str, Any]] = Field(default_factory=list)
    approval: Approval | None = None
    reopens: list[Reopen] = Field(default_factory=list)
    archived: bool = False

    def following_stage(self) -> str | None:
        """Etapa que sigue a la actual según el modo, o None si es la última."""
        return schema.next_stage(self.stage, self.mode)


class Research:
    """Investigación en disco: raíz + metadata."""

    def __init__(self, root: Path, meta: ResearchMeta) -> None:
        self.root = resolve_root(root)
        self.meta = meta

    @classmethod
    def create(
        cls,
        base: str | Path,
        slug: str,
        title: str,
        question: str,
        mode: str = "full",
        owner: str = "",
        timebox: int = 0,
        tags: list[str] | None = None,
    ) -> Research:
        """Crea la estructura de `research/<slug>/` con `sdr.yaml` inicializado."""
        if not is_valid_slug(slug):
            raise ValueError(f"slug inválido (debe ser kebab-case): {slug!r}")
        if mode not in schema.MODES:
            raise ValueError(f"modo desconocido: {mode!r}")
        base = resolve_root(base)
        root = resolve_segment(base, slug)
        if root.exists():
            raise FileExistsError(f"la investigación {slug!r} ya existe")
        root.mkdir(parents=True)
        for sub in _STAGE_DIRS:
            (root / sub).mkdir()
        meta = ResearchMeta(
            slug=slug,
            title=title,
            question=question,
            mode=mode,
            owner=owner,
            timebox=timebox,
            tags=list(tags or []),
            schema_version=2,
        )
        research = cls(root, meta)
        research.save()
        return research

    @classmethod
    def load(cls, root: str | Path, *, within: str | Path | None = None) -> Research:
        """Carga una investigación desde su directorio."""
        root = resolve_root(root)
        if within is not None:
            root = ensure_within(within, root)
        meta_path = resolve_child(root, META_FILE)
        raw = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
        meta = ResearchMeta.model_validate(raw)
        if not is_valid_slug(meta.slug):
            raise ValueError(f"slug inválido en {META_FILE}: {meta.slug!r}")
        return cls(root, meta)

    def save(self) -> None:
        """Persiste la metadata en `sdr.yaml`."""
        self.meta.updated = date.today().isoformat()
        data = self.meta.model_dump(mode="json", exclude_none=True)
        self.artifact_path(META_FILE).write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    def advance_stage(self) -> None:
        """Avanza a la siguiente etapa o marca la investigación como done.

        No ejecuta gates; solo muta el estado. La verificación de gates ocurre
        en la capa de CLI antes de invocar este método.
        """
        nxt = self.meta.following_stage()
        if nxt is None:
            self.meta.status = "done"
        else:
            self.meta.stage = nxt
        self.save()

    def artifact_path(self, relative: str) -> Path:
        """Ruta absoluta a un artefacto relativo dentro de la investigación."""
        path = resolve_child(self.root, relative)
        if path.is_dir():
            ensure_tree_within(self.root, path)
        return path

    def to_dict(self) -> dict[str, Any]:
        return self.meta.model_dump(mode="json", exclude_none=True)
