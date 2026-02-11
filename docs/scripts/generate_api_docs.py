from __future__ import annotations

import textwrap
from pathlib import Path

from pydoc_markdown import PydocMarkdown
from pydoc_markdown.contrib.loaders.python import PythonLoader
from pydoc_markdown.contrib.processors.crossref import CrossrefProcessor
from pydoc_markdown.contrib.processors.filter import FilterProcessor
from pydoc_markdown.contrib.processors.smart import SmartProcessor
from pydoc_markdown.contrib.renderers.markdown import MarkdownRenderer


API_MODULES: list[tuple[str, str, int]] = [
    # Core
    ("display", "display", 10),
    ("surface", "Surface", 20),
    ("rect", "Rect / FRect", 30),
    ("color", "Color", 40),
    ("draw", "draw", 50),
    ("event", "event", 60),
    ("font", "font", 70),
    ("image", "image", 80),
    ("time", "time", 90),
    ("key", "key", 100),
    ("mouse", "mouse", 110),
    ("mask", "Mask", 120),
    ("transform", "transform", 130),
    ("sprite", "sprite", 140),
    ("math", "math", 150),
    # Extras
    ("gfxdraw", "gfxdraw", 200),
    ("surfarray", "surfarray", 210),
    ("pixelcopy", "pixelcopy", 220),
    ("constants", "constants", 230),
    # Stubs
    ("camera", "camera", 300),
    ("cursors", "cursors", 310),
    ("freetype", "freetype", 320),
    ("midi", "midi", 330),
    ("sndarray", "sndarray", 340),
]

ROOT = Path(__file__).resolve().parent.parent.parent  # ipygame repo root
DOCS = ROOT / "docs"
OUT_DIR = DOCS / "src" / "content" / "docs" / "api"

STUB_MODULES = {"camera", "cursors", "freetype", "ftfont", "midi", "sndarray"}

def generate_module_md(module_name: str) -> str:
    session = PydocMarkdown(
        loaders=[PythonLoader(modules=[f"ipygame.{module_name}"], search_path=[str(ROOT)])],
        processors=[
            FilterProcessor(
                skip_empty_modules=False,
                documented_only=False,
                exclude_private=True,
                exclude_special=True,
                expression=(
                    "default() and obj.__class__.__name__ != 'Indirection' and "
                    "(not name.startswith('__') or name == '__init__')"
                ),
            ),
            SmartProcessor(),
            CrossrefProcessor(),
        ],
        renderer=MarkdownRenderer(
            render_module_header=True,
            render_toc=False,
            data_code_block=True,
        ),
    )
    modules = session.load_modules()
    session.process(modules)
    return session.renderer.render_to_string(modules)


def make_frontmatter(module_name: str, label: str, order: int) -> str:
    is_stub = module_name in STUB_MODULES
    description = (
        f"API reference for the ipygame.{module_name} module (stub)."
        if is_stub
        else f"API reference for the ipygame.{module_name} module."
    )
    lines = [
        "---",
        f"title: ipygame.{module_name}",
        f"description: {description}",
        f"sidebar:",
        f"  order: {order}",
    ]
    if is_stub:
        lines.append(f'  badge: "Stub"')
    lines.append("---")
    return "\n".join(lines)


def postprocess(body: str, module_name: str) -> str:
    lines = body.splitlines()
    out: list[str] = []
    for line in lines:
        if line.startswith("# ipygame."):
            continue
        if line.strip() == f'<a id="ipygame.{module_name}"></a>':
            continue
        out.append(line)

    while out and not out[0].strip():
        out.pop(0)

    return "\n".join(out) + "\n"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for module_name, label, order in API_MODULES:
        print(f"Generating docs for ipygame.{module_name} ...")
        body = generate_module_md(module_name)
        if not body.strip():
            print(f"  SKIP (no output)")
            continue
        body = postprocess(body, module_name)
        frontmatter = make_frontmatter(module_name, label, order)
        content = frontmatter + "\n\n" + body
        out_path = OUT_DIR / f"{module_name}.md"
        out_path.write_text(content, encoding="utf-8")
        print(f"  -> {out_path.relative_to(ROOT)}")

    index_content = textwrap.dedent("""\
        ---
        title: API Reference
        description: Complete API reference for all ipygame modules.
        sidebar:
          order: 0
        ---

        This section contains the auto-generated API reference for every
        public module in **ipygame**.

        <Aside>For a detailed documentation of all of the functions please have a look at the API reference from `pygame-ce`: https://pyga.me/docs/.
        ipygame cannot implement all available functions from pygame. Please have a look at the API coverage document as well. </Aside>

        ## Core Modules

        | Module | Description |
        |--------|-------------|
        | [display](display/) | Create and manage the display surface |
        | [Surface](surface/) | 2-D image stored as a NumPy RGBA pixel buffer |
        | [Rect / FRect](rect/) | Rectangle classes for positioning and collision |
        | [Color](color/) | RGBA color with rich conversion support |
        | [draw](draw/) | Shape-drawing functions |
        | [event](event/) | Event queue and input events |
        | [font](font/) | TrueType font rendering |
        | [image](image/) | Image loading and saving |
        | [time](time/) | Clock and timing utilities |
        | [key](key/) | Keyboard state and key constants |
        | [mouse](mouse/) | Mouse state and cursor |
        | [Mask](mask/) | Bitmask for pixel-perfect collision |
        | [transform](transform/) | Surface transformations (scale, rotate, blur, …) |
        | [sprite](sprite/) | Sprite and Group classes |
        | [math](math/) | Vector2 and Vector3 |

        ## Additional Modules

        | Module | Description |
        |--------|-------------|
        | [gfxdraw](gfxdraw/) | Anti-aliased and filled primitives |
        | [surfarray](surfarray/) | NumPy array access to pixel data |
        | [pixelcopy](pixelcopy/) | Low-level pixel copy utilities |
        | [constants](constants/) | All pygame constants (keys, events, flags) |

        ## Stub Modules

        These modules exist for import compatibility but raise
        `NotImplementedError` when used.

        | Module | Description |
        |--------|-------------|
        | [camera](camera/) | Camera capture (not available in Jupyter) |
        | [cursors](cursors/) | Hardware cursors |
        | [freetype](freetype/) | FreeType font rendering |
        | [midi](midi/) | MIDI input / output |
        | [sndarray](sndarray/) | Sound sample arrays |
    """)
    index_path = OUT_DIR / "index.md"
    index_path.write_text(index_content, encoding="utf-8")
    print(f"  -> {index_path.relative_to(ROOT)}")
    print("Done.")


if __name__ == "__main__":
    main()
