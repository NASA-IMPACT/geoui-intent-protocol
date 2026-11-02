"""Export the protocol's JSON Schemas to ``schemas/`` from the pydantic models.

pydantic is the single source of truth for the GeoUI document shape; the
committed JSON is what non-Python consumers (the ``@geoui/react-adapter`` SDK, any
other adapter) read, and ``schemas/`` is also what ``.github/workflows/pages.yml``
publishes as the root of ``SCHEMAS_BASE_URL``, so every file's path is its URL.

- ``schemas/geo_intent.json`` is ``GeoIntent``'s JSON Schema.
- ``schemas/ext/<prefix>/v<version>/schema.json`` is each shipped extension's
  ``ExtensionSpec.schema_document()``: the fields' JSON Schema with ``$id`` =
  the extension URI and the ``describe()`` metadata under ``x-geoui``.
- ``schemas/index.html`` lists them, so the site root is not a 404.

``tests/test_schemas.py`` fails when the files drift. **A published version
never changes**: when a change to an extension's fields drifts an existing
``v<version>`` document, bump that extension's ``VERSION`` (a new directory and
a new URI) instead of rewriting the old one. Older directories stay as they
are; this script never deletes.

Examples::

    uv run python scripts/export_schemas.py            # (re)write schemas/
    uv run python scripts/export_schemas.py --check    # exit 1 and list drifted files
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

from geoui.core import GeoIntent
from geoui.extensions import ALL
from geoui.extensions.spec import SCHEMAS_BASE_URL

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = ROOT / "schemas"


def index_html() -> str:
    """A static listing of the published documents, served at the site root."""
    rows = "".join(
        f'      <li><a href="{spec.schema_path}">{html.escape(spec.uri)}</a> &mdash; {html.escape(spec.summary)}</li>\n'
        for spec in ALL
    )
    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        "  <title>GeoUI Intent Protocol schemas</title>\n"
        "</head>\n"
        "<body>\n"
        "  <h1>GeoUI Intent Protocol schemas</h1>\n"
        '  <p>JSON Schemas of the <a href="https://github.com/NASA-IMPACT/geoui-intent-protocol">GeoUI Intent Protocol</a>.'
        " Each extension URI below is the address of its own <code>schema.json</code>; a published version never changes.</p>\n"
        f'  <p>Core document: <a href="geo_intent.json">{html.escape(SCHEMAS_BASE_URL)}/geo_intent.json</a></p>\n'
        "  <h2>Extensions</h2>\n"
        "  <ul>\n"
        f"{rows}"
        "  </ul>\n"
        "</body>\n"
        "</html>\n"
    )


def generated() -> dict[Path, str]:
    """Every file under ``schemas/`` this version of the library produces, as ``{path: text}``."""
    docs: dict[Path, dict] = {SCHEMAS_DIR / "geo_intent.json": GeoIntent.model_json_schema()}
    for spec in ALL:
        docs[SCHEMAS_DIR / spec.schema_path] = spec.schema_document()
    files = {path: json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n" for path, doc in docs.items()}
    files[SCHEMAS_DIR / "index.html"] = index_html()
    return files


def drifted() -> list[Path]:
    """Files whose committed text differs from the generated one (missing files count)."""
    return [p for p, text in generated().items() if not p.exists() or p.read_text() != text]


def write() -> list[Path]:
    out = []
    for path, text in generated().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        out.append(path)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true", help="report drift instead of writing")
    args = parser.parse_args(argv)
    if args.check:
        bad = drifted()
        for p in bad:
            print(f"drifted: {p.relative_to(ROOT)}")
        if bad:
            print("run: uv run python scripts/export_schemas.py")
            if any(p.parent.name.startswith("v") and p.exists() for p in bad):
                print("a published ext/<name>/v<version>/ document never changes: bump VERSION instead of rewriting it")
        return 1 if bad else 0
    for p in write():
        print(f"wrote {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
