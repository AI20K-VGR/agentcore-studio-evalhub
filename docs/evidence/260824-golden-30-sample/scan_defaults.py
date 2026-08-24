"""Quét `golden_set_ref` mặc định ở MỌI nơi khai nó, bằng AST chứ không bằng grep.

Vì sao AST: một transcript `grep` dán vào README là ảnh chụp — nó không chạy lại được, và nó
không phân biệt nổi "route dùng chung một class body" với "mỗi route một class riêng". Bản này
đọc cấu trúc: có bao nhiêu class body, mỗi class khai mặc định gì, và route nào import từ đâu.
Ngày ai đó tách một class request mới ra với mặc định khác, file `raw/defaults.json` đổi theo —
không cần ai nhớ chạy lại `grep`.

Phát hiện gốc (kit — evalhub#43): hệ thống có HAI mặc định khác nhau, và ranh giới là
HTTP-vs-thư-viện, KHÔNG phải route-vs-route.
"""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[5]

_ROUTE_FILES = {
    "apps/studio": ["src/studio_app/routes/runs.py", "src/studio_app/routes/publish.py"],
}
_BUILDER_FILE = ("packages/workbench", "src/studio_workbench/builder.py")

_FIELD = "golden_set_ref"


def _head_sha(repo: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(_ROOT / repo), "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout.strip()


def _literal(node: ast.AST | None) -> object:
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except (ValueError, SyntaxError):
        return f"<không phải hằng: {ast.unparse(node)}>"


def scan_request_classes(path: Path) -> dict[str, object]:
    """Mọi ClassDef trong file + mặc định `golden_set_ref` của nó (None = class không khai field này).

    Không lọc theo base `BaseModel`: lọc theo base sẽ bỏ sót một class kế thừa gián tiếp, mà bỏ sót
    đúng là thứ phép quét này tồn tại để chống.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    classes: dict[str, object] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        default: object = None
        declares = False
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name) and stmt.target.id == _FIELD:
                declares = True
                default = _literal(stmt.value)
        classes[node.name] = {"declares_golden_set_ref": declares, "default": default}
    return classes


def scan_imports_from_runs(path: Path) -> list[str]:
    """Tên được import từ `studio_app.routes.runs` — bằng chứng route dùng CHUNG body hay không."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").endswith("routes.runs"):
            names.extend(alias.name for alias in node.names)
    return sorted(names)


def scan_route_handlers(path: Path) -> dict[str, str]:
    """Mỗi hàm route → tên kiểu của tham số `body`. Đây là chỗ nói thật route nào ăn class nào."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    handlers: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        for arg in node.args.args:
            if arg.arg == "body" and arg.annotation is not None:
                handlers[node.name] = ast.unparse(arg.annotation)
    return handlers


def scan_function_defaults(path: Path) -> dict[str, object]:
    """Hàm public nào nhận kwarg `golden_set_ref` và mặc định của nó."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: dict[str, object] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        args = node.args
        pairs = list(zip(args.args[len(args.args) - len(args.defaults) :], args.defaults, strict=True))
        pairs += list(zip(args.kwonlyargs, args.kw_defaults, strict=True))
        for arg, default in pairs:
            if arg.arg == _FIELD:
                found[node.name] = _literal(default)
    return found


def main() -> dict[str, object]:
    report: dict[str, object] = {"heads": {}, "http_layer": {}, "library_layer": {}}

    for repo in ("apps/studio", "packages/workbench", "packages/kb", "packages/evalhub"):
        report["heads"][repo] = _head_sha(repo)  # type: ignore[index]

    for repo, files in _ROUTE_FILES.items():
        for rel in files:
            path = _ROOT / repo / rel
            report["http_layer"][rel] = {  # type: ignore[index]
                "classes": scan_request_classes(path),
                "imported_from_routes_runs": scan_imports_from_runs(path),
                "handler_body_types": scan_route_handlers(path),
            }

    repo, rel = _BUILDER_FILE
    report["library_layer"][rel] = scan_function_defaults(_ROOT / repo / rel)  # type: ignore[index]

    distinct = {
        entry["default"]
        for file in report["http_layer"].values()  # type: ignore[union-attr]
        for entry in file["classes"].values()
        if entry["declares_golden_set_ref"]
    } | set(report["library_layer"][rel].values())  # type: ignore[index]
    report["distinct_defaults"] = sorted(str(value) for value in distinct)

    return report


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=2))
