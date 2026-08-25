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
  "placeholder": "E.g. Apoe...",
  "output": {
    "path": "subjects",
    "mode": "append",
    "tpl": {
      "subject": "Gene: $label",
      "subjectScheme": "$scheme",
      "valueURI": "$id"
    }
  }
}
```

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

---

## Output mapping

Every field that should persist data needs an `output` block:

| Key | Description |
|---|---|
| `path` | Destination key in the FDF JSON |
| `mode` | How to write: `set`, `append`, `set_int`, `collect_object`, `append_if`, etc. |
| `tpl` | Template for the output object (`$value`, `$label`, `$id` placeholders) |
| `obj_key` | Key inside a repeated object (for repeatable sections) |
| `xref_key` | Field name for cross-references |

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

### Taxon-based API routing

```json
{
  "api": "ensembl_allele",
  "api_by_taxon": {
    "10090": "mousemine_allele",
    "10116": "alliance_allele_search",
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
    "10090": "mousemine_allele",
    "10116": "alliance_allele_search"
  }
}
```

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
| `bind_to` | Copy value to a target attribute |
| `output.path` | Destination in FDF JSON |
| `output.mode` | Write mode (`set`, `append`, `collect_object`…) |
| `output.tpl` | Value mapping template |
| `output.obj` | Auxiliary fields for enrichment |
| `display_mapping` | Dataset page rendering rules |

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
- Added `phenotype_search` field to `sections.disease`
- Added `ols_upheno` API for UPheno ontology lookups
