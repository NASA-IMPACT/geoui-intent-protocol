import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { GENERATED_DIR, SCHEMAS_DIR, generate, specFromSchemaDocument } from "../../scripts/gen-types";
import { extensions } from "../extensions";

describe("generated files", () => {
  it("match a fresh run of gen-types (no drift)", async () => {
    const fresh = await generate();
    for (const [name, text] of Object.entries(fresh)) {
      expect(readFileSync(join(GENERATED_DIR, name), "utf8"), `${name} drifted: npm run gen:types`).toBe(text);
    }
  });
});

describe("extensions", () => {
  const compareDoc = JSON.parse(readFileSync(join(SCHEMAS_DIR, "ext/compare/v1.0.0/schema.json"), "utf8"));

  it("are the committed schema documents, verbatim", () => {
    expect(extensions.compare).toEqual(specFromSchemaDocument(compareDoc));
    expect(extensions.compare.scope).toBe("intent");
    expect(extensions.rasterStyling.scope).toBe("layer");
    expect(extensions.chart.keys).toContain("chart:layer");
    expect(extensions.compare.required).toEqual(["compare:layers"]);
  });

  it("carry the document's $id as their URI and its x-geoui metadata", () => {
    expect(extensions.compare.uri).toBe(compareDoc.$id);
    expect(extensions.compare.uri).toBe("https://nasa-impact.github.io/geoui-intent-protocol/ext/compare/v1.0.0/schema.json");
    expect(compareDoc["x-geoui"]).toEqual({
      name: extensions.compare.name,
      scope: extensions.compare.scope,
      summary: extensions.compare.summary,
      keys: extensions.compare.keys,
      required: extensions.compare.required,
    });
    expect(extensions.compare.fields_schema).not.toHaveProperty("$id");
    for (const spec of Object.values(extensions)) {
      // The URI is the address of the file: its tail is the path under schemas/.
      expect(spec.uri).toMatch(/^https:\/\/nasa-impact\.github\.io\/geoui-intent-protocol\/ext\/[a-z-]+\/v\d+\.\d+\.\d+\/schema\.json$/);
    }
  });
});
