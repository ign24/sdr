import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = PROJECT_ROOT / "src" / "sdr"


def _missing_public_annotations() -> list[str]:
    missing: list[str] = []
    for path in sorted(PACKAGE_ROOT.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        public_classes = {
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and not node.name.startswith("_")
        }
        functions = [
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not node.name.startswith("_")
        ]
        functions.extend(
            node
            for class_node in public_classes
            for node in class_node.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not node.name.startswith("_")
        )

        for function in functions:
            parameters = [
                *function.args.posonlyargs,
                *function.args.args,
                *function.args.kwonlyargs,
            ]
            parameters.extend(
                parameter
                for parameter in (function.args.vararg, function.args.kwarg)
                if parameter is not None
            )
            for parameter in parameters:
                if parameter.arg not in {"self", "cls"} and parameter.annotation is None:
                    missing.append(
                        f"{path.relative_to(PROJECT_ROOT)}:{function.lineno}:{parameter.arg}"
                    )
            if function.returns is None:
                missing.append(f"{path.relative_to(PROJECT_ROOT)}:{function.lineno}:return")
    return missing


def test_public_functions_have_complete_annotations() -> None:
    assert _missing_public_annotations() == []


def test_typed_package_marker_exists() -> None:
    assert (PACKAGE_ROOT / "py.typed").is_file()
