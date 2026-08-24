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
    except ValueError, SyntaxError:
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
        # `args.defaults` chỉ phủ ĐUÔI của `args.args` (tham số có mặc định luôn đứng cuối), còn
        # `args.kw_defaults` phủ đủ `kwonlyargs` nhưng cho `None` ở kwarg không mặc định — hai hình
        # khác nhau, nên ghép riêng rồi nối, và kiểu phần tử phải khai tường minh (`expr | None`).
        pairs: list[tuple[ast.arg, ast.expr | None]] = []
        positional = args.args[len(args.args) - len(args.defaults) :]
        pairs.extend(zip(positional, args.defaults, strict=True))
        pairs.extend(zip(args.kwonlyargs, args.kw_defaults, strict=True))
        for arg, default in pairs:
            if arg.arg == _FIELD:
                found[node.name] = _literal(default)
    return found


def main() -> dict[str, object]:
    # Ba repo NGOÀI, không có `packages/evalhub`: entry này nằm trong chính repo đó, nên SHA của nó
    # là tự chiếu — git đã ghi commit rồi, mà đưa vào đây thì `raw/defaults.json` đổi theo mỗi
    # commit và tạo ra một diff nhiễu không nói thêm điều gì.
    heads = {repo: _head_sha(repo) for repo in ("apps/studio", "packages/workbench", "packages/kb")}

    http_layer: dict[str, dict[str, object]] = {}
    for repo, files in _ROUTE_FILES.items():
        for rel in files:
            path = _ROOT / repo / rel
            http_layer[rel] = {
                "classes": scan_request_classes(path),
                "imported_from_routes_runs": scan_imports_from_runs(path),
                "handler_body_types": scan_route_handlers(path),
            }

    builder_repo, builder_rel = _BUILDER_FILE
    library_layer = {builder_rel: scan_function_defaults(_ROOT / builder_repo / builder_rel)}

    # Tập mặc định KHÁC NHAU đang tồn tại — dài hơn 1 phần tử nghĩa là hệ thống chưa chốt một
    # `golden_set_ref` mặc định, và mọi con số công bố phải khai mình đo trên bộ nào.
    distinct: set[str] = set()
    for file_report in http_layer.values():
        classes = file_report["classes"]
        assert isinstance(classes, dict)
        for entry in classes.values():
            if entry["declares_golden_set_ref"]:
                distinct.add(str(entry["default"]))
    for default in library_layer[builder_rel].values():
        distinct.add(str(default))

    return {
        "heads": heads,
        "http_layer": http_layer,
        "library_layer": library_layer,
        "distinct_defaults": sorted(distinct),
    }


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=2))
