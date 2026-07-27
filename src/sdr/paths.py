"""Resolución centralizada de rutas confinadas a una raíz explícita."""

from __future__ import annotations

import os
from pathlib import Path, PureWindowsPath


def resolve_root(root: str | Path) -> Path:
    """Normaliza una raíz configurable, absoluta o relativa."""
    return Path(root).expanduser().resolve(strict=False)


def resolve_child(root: str | Path, relative: str | Path) -> Path:
    """Resuelve una ruta relativa y exige que permanezca dentro de ``root``."""
    root_path = resolve_root(root)
    raw = os.fspath(relative)
    relative_path = Path(raw)
    if (
        relative_path.is_absolute()
        or PureWindowsPath(raw).is_absolute()
        or "\\" in raw
        or ".." in relative_path.parts
    ):
        raise ValueError(f"ruta relativa inválida: {raw!r}")

    return ensure_within(root_path, root_path / relative_path)


def ensure_within(root: str | Path, path: str | Path) -> Path:
    """Normaliza ``path`` y exige que quede confinado a ``root``."""
    root_path = resolve_root(root)
    candidate = Path(path).resolve(strict=False)
    if not candidate.is_relative_to(root_path):
        raise ValueError(f"ruta fuera de la raíz permitida {root_path}: {path!r}")
    return candidate


def ensure_tree_within(root: str | Path, directory: str | Path) -> Path:
    """Valida symlinks de un árbol sin seguir directorios enlazados."""
    root_path = resolve_root(root)
    directory_path = ensure_within(root_path, directory)
    for current, directories, files in directory_path.walk(follow_symlinks=False):
        for name in (*directories, *files):
            ensure_within(root_path, current / name)
    return directory_path


def resolve_segment(root: str | Path, segment: str) -> Path:
    """Resuelve un único nombre, rechazando cualquier separador de ruta."""
    if not segment or "/" in segment or "\\" in segment:
        raise ValueError(f"segmento inválido: {segment!r}")
    return resolve_child(root, segment)
