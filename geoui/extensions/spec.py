"""A self-describing record of one extension, for consumers that advertise what they support.

An application (or the tool layer in front of it) lists the
:class:`ExtensionSpec` objects it implements. From that list it can tell an
agent which extensions exist and what their fields are (``describe``),
pre-declare their URIs on incoming documents, and refuse namespaces it does
not implement (``used_prefixes``). The producer-side rule of the protocol,
"declare what you use", is then satisfied by the consumer that knows what it
accepts, instead of by every producer remembering the URI strings.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel

from geoui.core import GeoIntent

Scope = Literal["intent", "layer"]

#: Where the published schemas live: ``schemas/`` of the repository, served as the root of this
#: site by ``.github/workflows/pages.yml``. Every extension URI is the address of its own
#: ``schema.json`` there (``<base>/<schema_path>``).
SCHEMAS_BASE_URL = "https://nasa-impact.github.io/geoui-intent-protocol"
JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"
_DOCUMENT_ONLY_KEYS = ("$schema", "$id", "x-geoui")


def ext_uri(prefix: str, version: str) -> str:
    """The canonical URI of extension ``prefix`` at ``version``: ``<base>/ext/<prefix>/v<version>/schema.json``."""
    return f"{SCHEMAS_BASE_URL}/{_schema_path(prefix, version)}"


def _schema_path(prefix: str, version: str) -> str:
    return f"ext/{prefix}/v{version}/schema.json"


@dataclass(frozen=True)
class ExtensionSpec:
    """What an extension is: its URI, key prefix, version, where its fields live, and their typed model."""

    uri: str
    prefix: str
    scope: Scope
    fields: type[BaseModel]
    summary: str
    version: str

    @property
    def name(self) -> str:
        return self.prefix

    @property
    def schema_path(self) -> str:
        """Where the published document sits under ``schemas/`` (and under the site root): ``ext/<prefix>/v<version>/schema.json``."""
        return _schema_path(self.prefix, self.version)

    def keys(self) -> list[str]:
        """The namespaced keys a producer writes, e.g. ``compare:layers``."""
        return [f"{self.prefix}:{field}" for field in self.fields.model_fields]

    def describe(self) -> dict[str, Any]:
        """A plain dict an agent can read: name, uri, scope, summary, keys and the fields' JSON schema."""
        schema = self.fields.model_json_schema()
        return {
            "name": self.prefix,
            "uri": self.uri,
            "scope": self.scope,
            "summary": self.summary,
            "keys": self.keys(),
            "required": [f"{self.prefix}:{field}" for field in schema.get("required", [])],
            "fields_schema": schema,
        }

    def schema_document(self) -> dict[str, Any]:
        """The published ``schema.json``: the fields' JSON Schema with ``$id`` = the URI and the rest of
        :meth:`describe` under ``x-geoui``. :func:`spec_from_schema_document` inverts it.

        A version's document never changes once it is published; a change to the fields means a new
        ``version`` (and so a new URI and a new file).
        """
        described = self.describe()
        return {
            "$schema": JSON_SCHEMA_DIALECT,
            "$id": self.uri,
            "x-geoui": {key: described[key] for key in ("name", "scope", "summary", "keys", "required")},
            **described["fields_schema"],
        }


def spec_from_schema_document(doc: Mapping[str, Any]) -> dict[str, Any]:
    """The :meth:`ExtensionSpec.describe` dict of a published ``schema.json`` (a consumer that fetched the URI)."""
    meta = doc["x-geoui"]
    return {
        "name": meta["name"],
        "uri": doc["$id"],
        "scope": meta["scope"],
        "summary": meta["summary"],
        "keys": list(meta["keys"]),
        "required": list(meta["required"]),
        "fields_schema": {key: value for key, value in doc.items() if key not in _DOCUMENT_ONLY_KEYS},
    }


def used_prefixes(intent: GeoIntent) -> set[str]:
    """Every namespace prefix with at least one ``<prefix>:<field>`` key on the intent or on any layer."""
    found: set[str] = set()
    for key in intent.__pydantic_extra__ or {}:
        if ":" in key:
            found.add(key.split(":", 1)[0])
    for layer in intent.layers:
        for key in layer.__pydantic_extra__ or {}:
            if ":" in key:
                found.add(key.split(":", 1)[0])
    return found


def declare(intent: GeoIntent, uris: list[str] | tuple[str, ...]) -> GeoIntent:
    """Return a copy of ``intent`` that also declares ``uris`` (order kept, duplicates dropped). Does not mutate."""
    merged = list(intent.geoui_extensions)
    for uri in uris:
        if uri not in merged:
            merged.append(uri)
    if merged == list(intent.geoui_extensions):
        return intent
    base = intent.model_dump(by_alias=True)
    base["geoui_extensions"] = merged
    return GeoIntent.model_validate(base)


__all__ = [
    "SCHEMAS_BASE_URL",
    "ExtensionSpec",
    "Scope",
    "declare",
    "ext_uri",
    "spec_from_schema_document",
    "used_prefixes",
]
