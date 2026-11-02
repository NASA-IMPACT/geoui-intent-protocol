"""The committed JSON Schemas under ``schemas/`` are what the pydantic models generate (no drift)."""

import importlib.util
import json
from pathlib import Path

import jsonschema
import pytest

from geoui.extensions import ALL
from geoui.extensions.spec import SCHEMAS_BASE_URL, spec_from_schema_document

ROOT = Path(__file__).resolve().parents[1]


def _load_exporter():
    spec = importlib.util.spec_from_file_location("export_schemas", ROOT / "scripts" / "export_schemas.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


exporter = _load_exporter()


@pytest.mark.parametrize("path", sorted(exporter.generated()), ids=lambda p: str(p.relative_to(ROOT)))
def test_committed_schema_matches_generated(path):
    assert path.exists(), f"{path.relative_to(ROOT)} missing: run scripts/export_schemas.py"
    assert path.read_text() == exporter.generated()[path], (
        f"{path.relative_to(ROOT)} drifted: run scripts/export_schemas.py"
    )


def test_check_mode_is_clean():
    assert exporter.drifted() == []


@pytest.mark.parametrize("spec", ALL, ids=lambda s: s.prefix)
def test_extension_document_is_the_library_spec_at_its_own_uri(spec):
    doc = json.loads((exporter.SCHEMAS_DIR / spec.schema_path).read_text())
    # The URI is the address of the file: base + the path under schemas/ (which Pages serves as the root).
    assert doc["$id"] == spec.uri == f"{SCHEMAS_BASE_URL}/{spec.schema_path}"
    assert spec.schema_path == f"ext/{spec.prefix}/v{spec.version}/schema.json"
    assert doc["x-geoui"]["name"] == spec.prefix and doc["x-geoui"]["scope"] == spec.scope
    assert spec_from_schema_document(doc) == spec.describe()
    assert "$id" not in spec.describe()["fields_schema"]
    jsonschema.Draft202012Validator.check_schema(doc)


def test_index_lists_every_extension():
    index = (exporter.SCHEMAS_DIR / "index.html").read_text()
    for spec in ALL:
        assert f'href="{spec.schema_path}"' in index and spec.uri in index


def test_core_schema_is_geo_intent():
    doc = json.loads((exporter.SCHEMAS_DIR / "geo_intent.json").read_text())
    assert doc["title"] == "GeoIntent"
    assert set(doc["properties"]) >= {"geoui_version", "geoui_extensions", "viewport", "time", "layers"}
    assert doc["additionalProperties"] is True  # extension fields are namespaced extras
