from __future__ import annotations

import datetime
from pathlib import Path

import yaml

from pydoc_markdown import PydocMarkdown
from pydoc_markdown.contrib.loaders.python import PythonLoader


ROOT = Path(__file__).resolve().parent.parent.parent
DOCS = ROOT / "docs"
OUT_PATH = DOCS / "src" / "content" / "docs" / "api_coverage.md"
YAML_PATH = DOCS / "scripts" / "api_coverage.yml"

STATUS_LABELS = {
    "implemented": "✅",
    "not_implemented": "❌",
    "not_applicable": "🚫",
}


def _format_date(date: datetime.date) -> str:
    month = date.strftime("%B")
    return f"{month} {date.day}, {date.year}"


def _load_module(module_name: str):
    session = PydocMarkdown(
        loaders=[PythonLoader(modules=[module_name], search_path=[str(ROOT)])]
    )
    try:
        modules = session.load_modules()
    except Exception:
        return None
    return modules[0] if modules else None


def _iter_public_members(obj):
    members = getattr(obj, "members", None) or []
    for member in members:
        name = getattr(member, "name", "")
        if name.startswith("_"):
            continue
        yield member


def _collect_module_items(module_name: str, prefix: str) -> set[str]:
    module = _load_module(module_name)
    if module is None:
        return set()
    keys: set[str] = set()
    for member in _iter_public_members(module):
        kind = member.__class__.__name__
        if kind in {"Function"}:
            keys.add(f"{prefix}.{member.name}")
        elif kind == "Class":
            keys.add(f"{member.name}")
    return keys


def _collect_class_items(module_name: str, class_names: list[str]) -> set[str]:
    module = _load_module(module_name)
    if module is None:
        return set()
    keys: set[str] = set()
    for member in _iter_public_members(module):
        if member.__class__.__name__ != "Class":
            continue
        if member.name not in class_names:
            continue
        keys.add(member.name)
        for class_member in _iter_public_members(member):
            kind = class_member.__class__.__name__
            if kind == "Function":
                if class_member.name == "__init__":
                    continue
                keys.add(f"{member.name}.{class_member.name}")
            elif kind == "Variable":
                keys.add(f"{member.name}.{class_member.name}")
    return keys


def _infer_scan(title: str) -> dict[str, object] | None:
    if title == "Core Module (pygame)":
        return {"kind": "module", "module": "ipygame", "prefix": "pygame"}
    if title.startswith("pygame."):
        name = title.split("pygame.", 1)[1]
        if name in {"Surface", "Rect / FRect", "Color", "Window", "geometry", "system"}:
            if name == "Surface":
                return {"kind": "class", "module": "ipygame.surface", "classes": ["Surface"]}
            if name == "Rect / FRect":
                return {"kind": "class", "module": "ipygame.rect", "classes": ["Rect", "FRect"]}
            if name == "Color":
                return {"kind": "class", "module": "ipygame.color", "classes": ["Color"]}
            return None
        return {"kind": "module", "module": f"ipygame.{name}", "prefix": name}
    return None


def _default_label(key: str) -> str:
    if "." in key:
        left, right = key.split(".", 1)
        if left and left[0].isupper():
            if "." in right:
                return f"{left}.{right}"
            return f"{left}.{right}()"
        return f"{left}.{right}()"
    return f"{key}()"


def main() -> None:
    if not YAML_PATH.is_file():
        print(f"ERROR: {YAML_PATH} not found. Run bootstrap_api_coverage_yaml.py first.")
        raise SystemExit(1)

    data = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8")) or {}
    meta = data.get("meta", {})
    sections = data.get("sections", [])

    last_updated = meta.get("last_updated", "")

    lines: list[str] = [
        "---",
        f"title: {meta.get('title', 'API Coverage')}",
        f"description: {meta.get('description', 'Overview')}",
        "---",
        "",
        "This document provides a reference of the pygame-ce API and implementation status in ipygame.",
        "",
        "**Legend:**",
        "- ✅ **Implemented** - Function is fully implemented and tested",
        "- ❌ **Not Implemented** - Function is missing or stub only",
        "- 🚫 **Not Applicable** - Cannot be implemented in Jupyter environment",
        "",
        f"**Last Updated:** {last_updated}",
        "",
        "---",
        "",
        "## Table of Contents",
        "",
    ]

    def _anchor(title: str) -> str:
        slug = title.lower()
        slug = slug.replace("/", " ")
        slug = slug.replace(".", "")
        slug = slug.replace("(", "")
        slug = slug.replace(")", "")
        slug = slug.replace("  ", " ").strip()
        slug = "-".join(slug.split())
        return slug

    for section in sections:
        title = section.get("title", "")
        if title == "Table of Contents":
            continue
        lines.append(f"- [{title}](#{_anchor(title)})")

    lines.extend(["", "---", ""])

    for section in sections:
        title = section.get("title", "")
        if title == "Table of Contents":
            continue
        table_label = section.get("table_label", "Item")
        items = section.get("items", [])
        index: dict[str, dict[str, str]] = {
            item["key"]: item for item in items if "key" in item
        }

        scan = section.get("scan") or _infer_scan(title)
        if scan:
            kind = scan.get("kind")
            if kind == "module":
                module_name = scan.get("module")
                prefix = scan.get("prefix") or module_name.split(".")[-1]
                for key in sorted(_collect_module_items(module_name, prefix)):
                    if key not in index:
                        index[key] = {
                            "key": key,
                            "label": _default_label(key),
                            "status": "not_implemented",
                            "notes": "",
                        }
            elif kind == "class":
                module_name = scan.get("module")
                classes = scan.get("classes", [])
                for key in sorted(_collect_class_items(module_name, classes)):
                    if key not in index:
                        index[key] = {
                            "key": key,
                            "label": _default_label(key),
                            "status": "not_implemented",
                            "notes": "",
                        }

        lines.append(f"## {title}")
        lines.append("")
        lines.append(f"| {table_label} | Status | Notes |")
        lines.append("|----------|--------|-------|")

        for key, item in index.items():
            label = item.get("label", _default_label(key))
            status = item.get("status", "not_implemented")
            if status == "partial":
                status = "not_implemented"
            status_icon = STATUS_LABELS.get(status, "❌")
            notes = item.get("notes", "")
            lines.append(f"| `{label}` | {status_icon} | {notes} |")

        lines.extend(["", "---", ""])

    OUT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
