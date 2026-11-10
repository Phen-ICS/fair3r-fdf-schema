# FDF release and consumer contract

Version 3.0.9 adds configuration validation and corrects two schema-level semantic defects. It does not change the deployed CKAN loader or migrate existing datasets. Develop in the fork and submit changes to `Phen-ICS/fair3r-fdf-schema`; the production source remains upstream until operators explicitly change it.

## Validate before release

```sh
python -m pip install -r requirements-dev.txt
python tools/validate_schema.py
python -m unittest discover -s tests -v
python tools/i18n.py check --locale fr
```

The contract rejects unknown configuration properties, field types, mapper strategies and output modes. Python checks local and cross-section references, ambiguous identifiers, conditions, dependency cycles, output context, defaults and locale versions. Creator and contributor field IDs are scoped to their sections. The CKAN context names `organism_taxon_id` and `organism_ensembl_species`, and the virtual `organism_search` trigger, are explicit runtime exceptions.

Templates are checked for their declared shape. This validator does not execute the CKAN template language or external APIs. Successful validation establishes configuration consistency, not correct search results, dataset-level validity, ontology equivalence or lossless exports. PR checks remain offline; scheduled API reachability checks still need functional smoke tests.

## Build an immutable bundle

After committing and validating the intended release, run:

```sh
python tools/build_bundle.py --ref <full-40-character-commit-sha> --output-dir dist
```

The builder reads committed bytes, validates that snapshot, checks translation coverage, and writes a reproducible ZIP with the form definition, contract, sidecars, validation tools and dependency specification. It refuses branch names and overwriting an existing artifact. Uncommitted work is excluded. A commit predating the contract cannot be packaged with this builder.

`manifest.json` records `schema_id`, `schema_version`, `schema_sha` (the source Git commit), `schema_sha256` (the form file digest), and SHA-256 hashes of all payload files. Build using the dependencies specified by the selected revision. No release is published or deployed by this command. Hashes detect content mismatch; operators must obtain the commit and artifact from a trusted release source.

The `$id` is the logical upstream configuration identity. It is not an immutable retrieval location. Resolve historical definitions through the pinned commit or archived bundle, never through the current contents of `main`. The relative `$schema` points to the contract inside the same repository or bundle; validation loads the trusted local contract explicitly.

## Required CKAN implementation

These requirements need changes in `Phen-ICS/ckanext-fair3r` before production adoption:

1. Fetch a selected upstream commit or immutable release into a staging location. Check all payload hashes, validate against a trusted compatible contract, and check schema/runtime compatibility before installation. Replace the deployed bundle atomically. Retain its manifest and the previous known-good bundle; a failed fetch or validation leaves the deployed version active. Scheduled updates must use the same validation gate.
2. Persist `schema_id`, `schema_version` and `schema_sha` beside each dataset's `fdf_output_json`. Store the content digest as well when practical. Load and edit historical answers with their recorded definition. Do not infer a commit for existing datasets; mark provenance unknown until established from deployment records. Migration must be explicit, retain the original answers and record source and target versions.
3. Validate organism presence by a subject with `subjectScheme == "NCBITaxon"` and an identifier valid for that scheme. A PATO-only subject must fail. The local configuration contract cannot correct the backend's shared-array requiredness check.
4. Preserve unresolved literals and record resolution status in the richer metadata representation. Free-text chromosome locations, allele identifiers and mutation types now retain `subject` without generating `valueURI`. API-backed manual entries still need runtime identifier validation. Preserve all CRediT attribution independently of export limitations.
5. Add a separate mixed-sex cohort representation. `PATO:0001340` remains an individual biological sex term, now labelled Hermaphrodite. Do not automatically reinterpret historical selections of “Both (hermaphrodite)”; the researcher's intended meaning is ambiguous. The current single-sex field does not capture mixed-sex cohorts.
6. Introduce structured treatment instances with stable IDs and associated compound, protocol, dose/unit, route, frequency and duration. Preserve grouping through create, serialize, edit and reload, including two treatments with omitted optional values. Derive discovery subjects from those records. Keep the existing parallel arrays until schema and runtime support can be released together; associations cannot reliably be reconstructed by array position.
7. Run the existing CKAN pytest suite in its CI. Add golden examples through the actual DataCite, DCAT-AP, schema.org and Croissant converters. Validate XML against the supported DataCite XSD, compare identifiers and relationships, and report dropped metadata. Check the deployed XML generator before changing its XSD or fallback year. Review the generated summary's description type against its actual content.

The fork's CI validates configuration only. Passing it is not evidence that these consumer requirements have been implemented. No CKAN deployment or converter round-trip was exercised by this change.

## Follow-on interoperability work

Keep discovery and citation metadata in FDF; link versioned experimental packages and profiles through stable identifiers. MNMS, HCMO and domain applications should retain detailed study, subject, trial and measurement relationships. Follow-up work should define the identifier/scheme registry, profile links and provenance crosswalks, configure institutional publisher defaults, and implement a runtime publication-year default while retaining researcher overrides. Do not invent unsupported default-expression syntax in this configuration.
