# Fair3r FDF chema

**100% declarative JSON schema** that drives the Fair3R Dataset Form (FDF) — a guided wizard for creating and editing FAIR datasets in CKAN.

> All business logic, API integrations, conditional visibility, and output mapping live in this single file. The frontend builds the form from it; the backend reuses the same rules to validate and convert data.

---

## Quick start

```jsonc
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "version": "3.0.0",
  "meta": { ... },
  "apis": { ... },
  "vocabularies": { ... },
  "sections": [ ... ]
}
```

The file has three top-level blocks:

| Block | Purpose |
|---|---|
| **`apis`** | External data sources consumed by `api_search` fields |
| **`vocabularies`** | Reusable controlled lists (`select`, `multi_select`, presets) |
| **`sections`** | What the user sees — order, fields, conditions, output mapping |

---

## How it works

```
You edit fdf_schema.json
        │
        ▼
Frontend reads schema → builds form dynamically
        │
        ▼
User fills form → JSON output stored in fdf_output_json
        │
        ▼
Backend reads same schema → validates → maps to DataCite → publishes to CKAN
```

**One source of truth.** Change the JSON, everything updates.

---

## Reading the schema

### Minimal structure

```json
{
  "apis": {},
  "vocabularies": {},
  "sections": []
}
```

### Minimal working example

```json
{
  "vocabularies": {
    "yes_no": [
      { "value": "yes", "label": "Yes" },
      { "value": "no", "label": "No" }
    ]
  },
  "sections": [
    {
      "id": "general",
      "title": "General Information",
      "fields": [
        {
          "id": "title",
          "label": "Title",
          "type": "text",
          "required": true,
          "output": { "path": "titles", "mode": "append", "tpl": { "title": "$value" } }
        },
        {
          "id": "validated",
          "label": "Data validated",
          "type": "select",
          "vocabulary": "yes_no",
          "output": { "path": "notes", "mode": "set" }
        }
      ]
    }
  ]
}
```

---

## Field types reference

### `text` — short free-text field

```json
{
  "id": "my_text",
  "label": "Title",
  "type": "text",
  "required": true,
  "output": { "path": "title", "mode": "set" }
}
```

### `textarea` — long structured text

```json
{
  "id": "abstract",
  "label": "Abstract",
  "type": "textarea",
  "rows": 6,
  "output": {
    "path": "descriptions",
    "mode": "append",
    "tpl": { "description": "$value", "descriptionType": "Abstract" }
  }
}
```

### `number` — numeric with bounds

```json
{
  "id": "publication_year",
  "label": "Publication Year",
  "type": "number",
  "min": 2000,
  "max": 2030,
  "output": { "path": "publicationYear", "mode": "set_int" }
}
```

### `select` — single choice from fixed options

```json
{
  "id": "resource_type",
  "label": "Resource Type",
  "type": "select",
  "options": [
    { "value": "Dataset", "label": "Dataset" },
    { "value": "Image", "label": "Image" }
  ],
  "output": {
    "path": "types",
    "mode": "append",
    "tpl": { "resourceType": "$value" }
  }
}
```

### `checkbox_group` — boolean toggles that open sections

```json
{
  "id": "intervention_types",
  "label": "Select interventions",
  "type": "checkbox_group",
  "options": [
    {
      "value": "GENE",
      "label": "Genetic Modification",
      "opens_section": "genes"
    }
  ]
}
```

### `multi_select` — multiple selection from a vocabulary

```json
{
  "id": "contributor_roles",
  "label": "CRediT Roles",
  "type": "multi_select",
  "vocabulary": "credit_roles",
  "output": {
    "path": "contributors",
    "mode": "append_from_array"
  }
}
```

### `api_search` — remote search with manual fallback

```json
{
  "id": "gene_search",
  "label": "Gene Symbol",
  "type": "api_search",
  "api": "mygene",
  "allow_manual": true,
  "show_xrefs": true,
  "xref_concept": "Gene",
  "placeholder": "E.g. Apoe...",
  "output": {
    "path": "subjects",
    "mode": "append",
    "tpl": {
      "subject": "$label",
      "subjectScheme": "$scheme",
      "valueURI": "$id"
    }
  }
}
```

- **`show_xrefs`** — displays the selected result's cross-reference links (its mapper's `xrefs` / `xref_from_extra`, see [Mapper extras & cross-references](#mapper-extras--cross-references)) under the field
- **`xref_concept`** — labels which concept those cross-references belong to (e.g. `"Gene"`, `"Allele"`), so the app can group/tell apart the xrefs of two different `api_search` fields shown in the same repeatable row (e.g. `gene_search`'s MGI/RGD/ZFIN links vs. `allele_search`'s own MGI allele / Alliance links)
- Don't hardcode a label prefix into `subject` (e.g. `"Gene: $label"`) — write the raw value and let `display_mapping.labels[subjectScheme]` supply the prefix shown on the dataset page, see [Display mapping](#display-mapping)

### `preset_or_search` — quick presets + API fallback

```json
{
  "id": "organism_choice",
  "label": "Model Organism",
  "type": "preset_or_search",
  "vocabulary": "organism_presets",
  "search_api": "ols_ncbitaxon",
  "output": {
    "path": "subjects",
    "mode": "append",
    "tpl": {
      "subject": "$label",
      "subjectScheme": "NCBITaxon",
      "valueURI": "$id"
    }
  }
}
```

### Auto-filled but editable field (`bind_to`)

A plain field can be wired to copy a value out of a related `api_search` field's selected result, while staying editable — use this when auto-fill from the API isn't always reliable. `sections.genes.mutationType_display` is a real example: it's filled from whichever allele the user picked, but the user can type over it when the API had nothing useful:

```json
{
  "id": "allele_search",
  "type": "api_search",
  "api": "ensembl_allele",
  "update_display_field": "mutationType_display"
},
{
  "id": "mutationType_display",
  "label": "Mutation Type",
  "type": "text",
  "allow_manual": true,
  "dependent_on_field": "allele_search",
  "bind_to": "consequenceType || geneMutationType",
  "help": "Auto-filled from the allele search when the API provides it. If it stays empty or looks wrong, enter it manually."
}
```

- **`update_display_field`** (on the `api_search` field) — names the field that should receive data from the selected result
- **`bind_to`** (on the display field) — the key read from the selected result's `mapper.extra` (see [Mapper extras & cross-references](#mapper-extras--cross-references)); accepts a `"a || b"` fallback chain, tried in order, same as an output `tpl`
- **`dependent_on_field`** — the field that triggers the auto-fill, and whose changes should reset this one
- Leave off `readonly` (or set it `false`) so the field stays editable, and write a `help` text that tells the user when to fill it in themselves

---

## Output mapping

Every field that should persist data needs an `output` block:

| Key | Description |
|---|---|
| `path` | Destination key in the FDF JSON |
| `mode` | How to write: `set`, `append`, `set_int`, `collect_object`, `append_if`, etc. |
| `tpl` | Template for the output object (`$value`, `$label`, `$id` placeholders) |
| `obj_key` | Key inside a repeated object (for repeatable sections) |

Common modes:

- **`set`** — overwrite the path
- **`append`** — push to an array
- **`set_int`** — set as integer
- **`collect_object`** — gather all `obj_key` values into an array of objects
- **`append_if`** — append only if value is non-empty

---

## Display mapping

Control how data renders on the dataset page:

```json
"display_mapping": {
  "source": "subjects",
  "filter": { "subjectScheme": "GeneID" },
  "display_type": "list_links"
}
```

| Key | Description |
|---|---|
| `source` | Which output path(s) to read (`"subjects"`, `["subjects"]`, `"fundingReferences"`…) |
| `filter` | Restricts to matching entries, e.g. `{ "subjectScheme": "GeneID" }` or `{ "subjectScheme": [...] }` for several schemes at once (used by `composite` to pull multiple fields into one block) |
| `labels` | Maps each `subjectScheme` in `filter` to the label shown before its value on the dataset page (mainly for `composite`), e.g. `{ "geneAccessionId": "Gene" }` — this is why field `output.tpl.subject` should hold the raw value, not a hardcoded `"Gene: $label"` prefix |
| `display_type` | How the entries are rendered, see table below |

Available display types:

| Type | Use case |
|---|---|
| `composite` | Assembles multiple fields into one block |
| `authors_merged` | Merges creators and contributors |
| `descriptions` | Renders DataCite descriptions (Abstract, Methods…) |
| `list_links` | List with clickable URLs |
| `list_links_with_scheme` | Links with scheme labels (EFO, UBERON…) |
| `badges` | Short lists as visual tags |
| `text` | Raw text output |
| `related_identifiers` | Related resources table |

---

## Conditional visibility

### Section-level condition

```json
{
  "id": "genes",
  "condition": {
    "type": "checkbox_includes",
    "field_id": "intervention_types",
    "value": "GENE"
  }
}
```

### Field-level visibility

```json
{
  "id": "allele_search",
  "visible_if": {
    "field": "gene_search",
    "not_empty": true,
    "taxon_not_in": ["8364", "9544"]
  }
}
```

### Organism-trigger condition

```json
{
  "id": "strain",
  "condition": {
    "type": "organism_trigger",
    "trigger": "strain_search"
  }
}
```

---

## Repeatable sections

```json
{
  "id": "contributors",
  "title": "Contributors",
  "repeatable": true,
  "initial_instances": 0,
  "repeat_label": "Contributor",
  "add_label": "+ Add Contributor",
  "output": {
    "path": "contributors",
    "mode": "collect_object"
  },
  "fields": [ ... ]
}
```

- **`initial_instances`**: `0` = no pre-filled rows; `1` = one row shown by default
- Only works when `repeatable: true`

---

## Dynamic actions (`on_change`)

Trigger actions when a field value changes:

```json
{
  "id": "organism_choice",
  "on_change": [
    {
      "action": "reset_fields",
      "fields": ["gene_search", "allele_search", "strain_search"]
    }
  ]
}
```

Currently supported action: **`reset_fields`** — clears target fields and their API selections. Use when changing the organism to prevent stale gene/allele data.

---

## API configuration

Define external sources in the `apis` block:

```json
{
  "my_api": {
    "label": "MyGene.info",
    "url": "https://mygene.info/v3/query",
    "query_param": "q",
    "extra_params": {
      "fields": "symbol,name,taxid"
    },
    "extra_params_from_context": {
      "species": "organism_taxon_id"
    },
    "result_path": "hits",
    "result_limit": 8,
    "mapper": {
      "strategy": "flat_object",
      "label": "{{symbol}}",
      "sublabel": "{{name}}",
      "id": "https://identifiers.org/ncbigene:{{_id}}",
      "scheme": "geneAccessionId"
    }
  }
}
```

Key fields:

| Field | Description |
|---|---|
| `url` | API endpoint |
| `query_param` | Search parameter name |
| `extra_params` | Fixed query parameters |
| `extra_params_from_context` | Dynamic params from form fields |
| `path_params_from_context` | URL path variables from form fields |
| `result_path` | JSON path to results array |
| `result_limit` | Max results shown |
| `depends_on` | Parent field that must be filled first |
| `api_by_taxon` | Switch API based on selected organism |
| `mapper` | Transform API response → FDF item |

### Mapper strategies

- **`flat_object`** — flat result items
- **`nested_object`** — nested structure
- **`array`** — direct array mapping
- **`array_find`** — find-by-key strategy
- **`obo_ontology`** — OLS ontology format

### Mapper extras & cross-references

Beyond `label` / `sublabel` / `id` / `scheme`, a mapper can attach extra per-item data and describe how to link out to related records:

```json
"mapper": {
  "strategy": "array",
  "label": "{{symbolText || symbol || id}}",
  "id": "{{id}}",
  "scheme": "alleleAccessionId",
  "source_tag": "Alliance",
  "uri": "https://www.alliancegenome.org/allele/{{id}}",
  "id_candidates": [
    { "tpl": "https://identifiers.org/ncbigene:{{entrezgene}}" },
    { "tpl": "https://www.ensembl.org/id/{{ensembl.gene}}" }
  ],
  "xrefs": {
    "mgi": { "condition": "{{id}}", "id": "{{id}}", "label": "MGI", "uri": "https://www.informatics.jax.org/allele/{{id}}" }
  },
  "extra": {
    "alleleSymbol": "{{symbolText}}",
    "geneMutationType": "{{molecularConsequence[0] || variantType[0]}}"
  }
}
```

| Key | Description |
|---|---|
| `extra` | Per-item key/value data carried on the selected result; read later via `bind_to` on another field, or `$key` in this field's own `output.obj` |
| `uri` | Direct link template to the source database's own page for the selected item |
| `xrefs` | Named cross-reference links (`id`/`label`/`uri`, gated by `condition`) shown alongside the result, keyed by source (e.g. `mgi`, `alliance`) |
| `xref_from_extra` | Builds the cross-reference display from `extra` instead of a static `xrefs` block |
| `id_candidates` | Ordered fallback list of id templates, tried when the primary `id` template resolves empty (e.g. a gene missing `entrezgene`) |
| `detail_fetch` | After a result is selected, fetches a per-item detail endpoint and merges its data into `extra` (see below) |

### Detail fetch (secondary lookup after selection)

Sometimes the search endpoint itself can't carry the data you need — Alliance Genome's allele search tags every single allele with the same generic `alterationType` (`"allele"`), not its actual mutation description. `detail_fetch` lets a mapper fire a second request, scoped to the one result the user picked, and pull richer data from there:

```json
"mapper": {
  "strategy": "array",
  "extra": {
    "geneMutationType": "{{molecularConsequence[0] || variantType[0]}}"
  },
  "detail_fetch": {
    "url": "https://www.alliancegenome.org/api/allele/{{id}}",
    "extra": {
      "geneMutationType": "{{allele.relatedNotes.[?noteType.name=mutation_description].freeText}}"
    }
  }
}
```

- `url` — detail endpoint template, interpolated from the selected result's own fields (here `{{id}}`)
- `extra` — additional/override key-value pairs read from the detail response, using the same `{{...}}` templating (JMESPath-style filters included, e.g. `[?noteType.name=mutation_description]`) as the main mapper
- Keep a value in the main `mapper.extra` too when you can (as above) — it's what shows immediately, while `detail_fetch` fills in or overrides it once the second request resolves

Used by `alliance_allele_search_mouse` / `alliance_allele_search_rat` to pull the free-text `mutation_description` note from Alliance Genome's per-allele API, since the search endpoint alone can't tell a knockout from a point mutation.

Key fields at the API level (sibling of `mapper`, not inside it):

| Key | Description |
|---|---|
| `source_tag` / `dynamic_source_tag` | Labels which data source produced a result, shown as a badge; `dynamic_source_tag: true` lets the badge vary per result instead of being fixed to the API's own name |
| `exclude_categories` | Drops result categories the API returns but this field shouldn't show (e.g. `variant` on an allele search) |
| `query_prefix_with_gene` | Prefixes the search query with the selected gene symbol before calling the API |
| `provides_chromosome_location` | Marks an API (e.g. `mygene`) as a source for auto-filling `gene_chromosome_location` |
| `api_fallback` | Per-taxon list of backup APIs to try if the `api_by_taxon` API for that taxon fails or returns nothing |

### Taxon-based API routing

```json
{
  "api": "ensembl_allele",
  "api_by_taxon": {
    "10090": "alliance_allele_search_mouse",
    "10116": "alliance_allele_search_rat",
    "8364": "alliance_variant_search"
  }
}
```

The API automatically switches based on the selected organism's taxon ID.

### Server-side lookups

For APIs that must run on the backend (security/compatibility):

```json
{
  "xenbase_mutant_lines": {
    "label": "Xenbase Mutant Lines",
    "query_mode": "server_side_lookup",
    "provider": "xenbase",
    "resource": "gene_lines",
    "depends_on": "gene_search"
  }
}
```

---

## Vocabularies

Reusable controlled lists referenced by `select`, `multi_select`, and `preset_or_search`:

```json
{
  "vocabularies": {
    "credit_roles": {
      "label": "CRediT roles",
      "items": [
        { "id": "...", "label": "Conceptualization" },
        { "id": "...", "label": "Data Curation" }
      ]
    }
  }
}
```

The `organism_presets` vocabulary includes 15+ model organisms with emoji icons, taxon IDs, and Ensembl species mappings.

---

## Cross-reference catalog (`xref_catalog`)

A top-level dictionary that standardizes how allele/gene identifiers resolve to a source database and a clickable URI, independent of which field or API produced the id:

```json
"xref_catalog": {
  "MGI": {
    "db": "mgi",
    "label": "MGI",
    "uri": "https://www.informatics.jax.org/allele/MGI:{{id_suffix}}",
    "provider_aliases": ["MOUSE"]
  }
}
```

| Key | Description |
|---|---|
| `db` | Internal source key |
| `label` | Display label for the badge/link |
| `uri` | Link template; `{{id_suffix}}` is the identifier with its prefix (e.g. `MGI:`) stripped |
| `provider_aliases` | Alternate provider names, as returned by some APIs, that should resolve to this same entry |

Organism presets point into the catalog via `allele_source_label` (e.g. `"allele_source_label": "MGI"` on the mouse preset), so the UI knows which cross-reference database to prioritize for a given species.

---

## Practical changes

### Change a label or placeholder

Edit the field directly:

```json
{
  "id": "gene_search",
  "label": "Gene (symbol, name or ID)",
  "placeholder": "E.g. Apoe, MGI:88057"
}
```

### Add a new section

Add an object to the `sections` array:

```json
{
  "id": "funding",
  "title": "Funding Information",
  "icon": "$",
  "open_default": false,
  "fields": [
    {
      "id": "funder_name",
      "label": "Funder Name",
      "type": "text",
      "output": {
        "path": "fundingReferences",
        "mode": "append",
        "tpl": { "funderName": "$value" }
      }
    }
  ],
  "display_mapping": {
    "source": "fundingReferences",
    "display_type": "list"
  }
}
```

### Add a linked DOI field

```json
{
  "id": "linked_doi",
  "label": "Linked DOI",
  "type": "text",
  "placeholder": "10.1234/example.doi",
  "output": {
    "path": "relatedIdentifiers",
    "mode": "append",
    "tpl": {
      "relatedIdentifier": "$value",
      "relatedIdentifierType": "DOI",
      "relationType": "IsSupplementTo"
    }
  }
}
```

### Make a section conditional

```json
{
  "id": "sequencing",
  "condition": {
    "type": "checkbox_includes",
    "field_id": "intervention_types",
    "value": "SEQ"
  }
}
```

### Change the API per taxon

```json
{
  "id": "allele_search",
  "type": "api_search",
  "api": "ensembl_allele",
  "api_by_taxon": {
    "10090": "alliance_allele_search_mouse",
    "10116": "alliance_allele_search_rat"
  }
}
```

### Add an auto-filled but editable field

Pair an `api_search` field with a `text` field the user can still type into when the API doesn't have the data — see [Auto-filled but editable field](#auto-filled-but-editable-field-bind_to) for the full explanation:

```json
{
  "id": "allele_search",
  "type": "api_search",
  "api": "my_allele_api",
  "update_display_field": "mutation_type"
},
{
  "id": "mutation_type",
  "label": "Mutation Type",
  "type": "text",
  "allow_manual": true,
  "dependent_on_field": "allele_search",
  "bind_to": "geneMutationType",
  "help": "Auto-filled when the API provides it; enter manually otherwise."
}
```

Make sure the API's `mapper.extra` actually sets the key referenced by `bind_to` (here `geneMutationType`) — otherwise the field will just stay empty and rely entirely on manual entry.

---

## Glossary of JSON keys

| Key | Meaning |
|---|---|
| `condition` | Visibility condition for a section |
| `visible_if` | Visibility condition for a field |
| `repeatable` | Section can be repeated |
| `initial_instances` | Pre-filled rows for repeatable sections |
| `depends_on` | Parent field required before API query |
| `api` | Default API for `api_search` fields |
| `api_by_taxon` | Dynamic API selection by organism |
| `query_mode` | Special query mode (`server_side_lookup`, etc.) |
| `on_change` | Actions triggered on field change |
| `bind_to` | Reads a key (or `"a || b"` fallback chain) from a related result's `mapper.extra` into this field's value, editable unless `readonly` |
| `update_display_field` | On an `api_search` field: which field to push the selected result's `extra` data into |
| `dependent_on_field` | The field whose selection/change drives this field's auto-fill or reset |
| `show_xrefs` | On an `api_search` field: display the selected result's cross-reference links under the field |
| `xref_concept` | On an `api_search` field: labels which concept (`"Gene"`, `"Allele"`…) its cross-references belong to, so several such fields in the same row don't get their xrefs mixed up |
| `mapper.extra` | Per-item key/value data carried on an API result, read via `bind_to` or `$key` in `output.obj` |
| `mapper.xrefs` / `xref_from_extra` | Cross-reference links shown for a result, static or derived from `extra` |
| `mapper.id_candidates` | Fallback `id` templates tried in order when the primary one resolves empty |
| `mapper.detail_fetch` | Secondary API call, scoped to the selected result, to enrich `extra` with data the search endpoint didn't provide |
| `source_tag` / `dynamic_source_tag` | Badge naming the data source of a result; dynamic variant varies per result |
| `exclude_categories` | Result categories to drop from an API response |
| `query_prefix_with_gene` | Prefixes the search query with the selected gene symbol |
| `provides_chromosome_location` | Flags an API as a source for gene chromosome location auto-fill |
| `api_fallback` | Per-taxon backup APIs tried if the routed `api_by_taxon` API fails |
| `xref_catalog` | Top-level dictionary standardizing id → source database → URI resolution |
| `output.path` | Destination in FDF JSON |
| `output.mode` | Write mode (`set`, `append`, `collect_object`…) |
| `output.tpl` | Value mapping template |
| `output.obj` | Auxiliary fields for enrichment |
| `display_mapping` | Dataset page rendering rules |
| `display_mapping.labels` | Maps a `subjectScheme` to the label shown before its value on the dataset page — keep the prefix here, not baked into `output.tpl.subject` |

---

## Debugging checklist

### API field returns nothing

1. Verify organism is selected
2. Check `depends_on` (parent field filled?)
3. Check `api_by_taxon` (taxon mapped?)
4. Check `result_path` and `mapper` in the API definition
5. Ensure `allow_manual: true` for fallback

### Value visible in form but missing in output

1. Check `output.path`
2. Check `output.mode`
3. Verify template placeholders (`$value`, `$label`, `$id`)
4. Check `append_if` — may skip empty values

### Value in JSON but not shown on dataset page

1. Check `display_mapping.source`
2. Check `display_mapping.display_type`
3. Check `filter` — may be too restrictive

### DataCite mapping missing

1. Check the field's `output` mapping
2. Check normalization in `lib/fdf/datacite_converter.py`
3. Verify expected type (array / object / string)

---

## Best practices

- **Unique IDs** — avoid collisions between fields
- **Always define `output`** — without it, values are visual only, not persisted
- **Add `display_mapping`** — data exists but won't show without it
- **`allow_manual: true`** on critical `api_search` fields — keeps form usable when APIs are down
- **`depends_on` / `dependent_on_field`** — prevents invalid queries and guides users
- **`on_change.reset_fields`** — cleans stale values after parent changes
- **Test in both create and edit modes**

---

## Supported organisms

The schema includes presets for 15+ model organisms:

🐭 Mouse · 🐀 Rat · 🐹 Golden hamster · 🐟 Zebrafish · 🐟 Medaka · 🪰 Fruit fly · 🪱 C. elegans · 🐸 Xenopus · 🐒 Primates (Rhesus, Cynomolgus, Marmoset, Baboon, Vervet) · 🐇 Rabbit · 🐇 Pika · + custom NCBI Taxonomy search

---

## Pre-merge checklist

- [ ] Section/field visible per conditions, API search functional
- [ ] `fdf_output_json` contains expected data
- [ ] `display_mapping` renders data on dataset page
- [ ] DataCite mapping present (`subjects`, `creators`, `relatedIdentifiers`…)
- [ ] Translations updated: `python tools/i18n.py check --locale fr`
- [ ] Linting passes: `ruff check` and `bandit -r ckanext -x ckanext/fair3r/tests`

---

## Translations

User-facing labels, help text, and placeholders are **English-only** in
`fdf_schema.json`. Translations live in sidecar files under `i18n/` (separate
from CKAN Babel). CKAN downloads them via `fair3r update-schema`.

After editing the schema:

```bash
python tools/i18n.py template --locale fr   # add new keys, keep existing translations
python tools/i18n.py check --locale fr      # fail if any key is missing or empty
```

Sidecar keys use stable schema ids, for example
`sections.title.fields.publication_year.help`. If a translation is missing at
runtime, the English string from `fdf_schema.json` is shown.

To add a new locale, create `i18n/<locale>.json` using the same format and ask
the CKAN extension maintainers to add the locale to `SUPPORTED_SCHEMA_LOCALES`.

---

## Changelog

Add an entry here for each significant schema change:

```markdown
## [YYYY-MM-DD]
- Added section XXX
- Added taxon YYYY to organism_presets
- Changed api_by_taxon for allele_search
- Updated display_mapping for section ZZZ
```

## [2026-08-25]
- Added `phenotype_search` field to `sections.disease` — enables searching observable phenotypes and traits via the UPheno ontology, complementing disease modeling with observed characteristics (e.g. weight loss, splenomegaly, motor deficits)
- Added `ols_upheno` API — connects to the UPheno ontology through OLS4 for phenotype lookups

## [2026-08-28]
- Migrated allele search off MouseMine and per-gene lookup endpoints onto the Alliance Genome search API: replaced `mousemine_allele` / `mousemine_allele_bygene` with `alliance_allele_search_mouse`, replaced `alliance_allele_bygene` with `alliance_allele_search_rat` and `alliance_allele_search_danio`, and renamed `alliance_allele_search` to `alliance_allele_search_dmel`; added a new `alliance_allele_search_cel` API for C. elegans
- Removed the unused `eva_allele` and `rgd_rat_allele` APIs
- Added a top-level `xref_catalog` (MGI, RGD, ZFIN, FB, XENBASE, WB, ENS) defining `db`/`label`/`uri` templates and `provider_aliases`, plus an `allele_source_label` per organism preset, to standardize how allele cross-references are resolved and displayed
- Added `uri` links to `mygene` xrefs (NCBI Gene, MGI, RGD, ZFIN, Ensembl, FlyBase, WormBase, Xenbase), an `id_candidates` fallback list for more robust gene ID resolution, and a `provides_chromosome_location` flag
- Added `source_tag` / `dynamic_source_tag` and `xref_from_extra` to allele-search API mappers for consistent source attribution
- Updated `xenbase_mutant_lines` to resolve strains via `gene_search.xref:xenbase` instead of a separate context lookup, and simplified its output mapping to `lineType` / `lineId`
- Updated `sections.genes.allele_search`'s `api_by_taxon` to point to the new per-species Alliance search APIs, with an `api_fallback` to `ensembl_allele` for Xenopus
- Removed remaining "MouseMine" wording from `alliance_allele_search_mouse`'s label and from the `allele_search` field help text (MouseMine is down; mouse allele lookups now go through Alliance Genome only)
- Merged the two `sections.genes` mutation-type fields into one: `mutationType_display` is now a single editable field, visible for every organism, still auto-filled from the allele search when the API provides it (reliable for mouse/rat; most other allele-search APIs never populate it), but the user can now type or correct it manually when it doesn't. Removed the primates-only `mutation_type_free` field
- Added common mutation type examples to `mutationType_display`'s help text (missense_variant, nonsense_variant, frameshift_variant, deletion, insertion, duplication, inversion, splice_site_variant, synonymous_variant, knockout, knock-in, conditional knockout)
- Fixed mutation-type auto-fill in the 5 `alliance_allele_search_*` APIs (mouse, rat, danio, dmel, cel): `alterationType` — used since the Alliance migration — always equals the literal string `"allele"` (or `"allele with one variant"`), it's a category, not a mutation description, so auto-fill was silently wrong for mouse/rat and always empty for the others. `consequenceType`/`geneMutationType` now read `molecularConsequence[0] || variantType[0]` instead, which carries the real value (e.g. `missense_variant`, `stop_gained`, `point_mutation`) when the Alliance API has variant-level data for that allele, and stays empty otherwise (letting the user fill `mutationType_display` manually, as intended)
- Added a `detail_fetch` to the `alliance_allele_search_mouse` / `alliance_allele_search_rat` mappers: after an allele is selected, it calls `https://www.alliancegenome.org/api/allele/{{id}}` and pulls the free-text `mutation_description` note into `geneMutationType`/`consequenceType`, giving mouse and rat a real mutation description instead of relying only on `molecularConsequence`/`variantType` (which the search endpoint often doesn't return for allele-level results)
- Bumped schema version to 3.0.2

## [2026-08-31]
- Added `xref_concept` to `gene_search` (`"Gene"`) and `allele_search` (`"Allele"`) — tags which concept a field's cross-references belong to, so the app can label/group the Gene xrefs (MGI, RGD, ZFIN…) separately from the Allele xrefs (MGI allele page, Alliance…) when both are shown for the same gene/allele row
- Removed `gene_search`'s `output.xref_key: "identifiers"`, superseded by `xref_concept`
- `mutationType_display`'s `bind_to` now reads `"consequenceType || geneMutationType"` instead of just `"geneMutationType"`, so it also picks up the value when only `consequenceType` was populated (e.g. before a `detail_fetch` resolves)
- Fixed the top-level schema `version` field, which was still `3.0.0` while `meta.changelog` had already moved to `3.0.2`
- Fixed `xenopus_line_type` (the Xenbase "Line Type" field) never actually persisting its value: it had a `bind_to` for display but no `output` block of its own, and the `lineType` it was folded into on `genetic_background` wasn't wired to a subject either. It now writes its own `"Line type: $value"` subject with `subjectScheme: "lineType"`, added to the `genes` section's `display_mapping` filter/labels so it shows up on the dataset page
- Removed `allele_search`'s dead `output.obj.geneMutationType: "$mutation_type"` mapping — it referenced a key no API ever populates, and mutation type is now handled entirely by the dedicated `mutationType_display` field
- Bumped schema version to 3.0.3

## [2026-09-01]
- Removed the hardcoded label prefixes (`"Strain: $label"`, `"Gene: $label"`, `"Transgene origin: $label"`, `"Gene locus: $value"`, `"Allele: $label"`, `"Line type: $value"`, `"Mutation type: $value"`) from the `subject` templates across the `strain` and `genes` sections — the raw value is now written as-is, since the dataset page already shows each subject's label from `display_mapping.labels`/`subjectScheme`, so the old prefix just duplicated it
- Gave the Xenopus `genetic_background` field (Xenbase mutant/transgenic line search) its own `xenopusStrainLine` subject scheme instead of reusing the mouse/rat `strain` section's `speciesBackground` scheme; added it to the `genes` section's `display_mapping` filter and labels as "Strain / Line"
- Bumped schema version to 3.0.4
