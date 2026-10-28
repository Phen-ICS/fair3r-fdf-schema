#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 CNRS
# SPDX-License-Identifier: CECILL-B
"""Validate FDF configuration syntax, references and locale compatibility."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "schema/fdf-contract.schema.json"
# These are context values supplied by the existing CKAN runtime, not fields.
CONTEXT_KEYS = {"organism_taxon_id", "organism_ensembl_species"}
VIRTUAL_TRIGGERS = {"organism_search"}


def load_json(path: Path):
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_keys)


def validate(config: dict, locales: dict | None = None) -> list[str]:
    """Return actionable errors; never resolve the instance's $schema remotely."""
    contract = load_json(CONTRACT)
    Draft202012Validator.check_schema(contract)
    errors = [
        f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
        for e in Draft202012Validator(contract).iter_errors(config)
    ]
    if errors:
        return errors  # Reference checks require structurally valid objects.

    sections = config["sections"]
    section_ids = {s["id"] for s in sections}
    fields = defaultdict(list)
    for section in sections:
        for field in section["fields"]:
            fields[field["id"]].append((section["id"], field))

    def duplicate_ids(values, where):
        for value, count in Counter(values).items():
            if count > 1:
                errors.append(f"{where}: duplicate id {value!r}")

    duplicate_ids([s["id"] for s in sections], "sections")

    def resolve(name, where, local=None):
        if local and name in local:
            return local[name]
        matches = fields.get(name, [])
        if len(matches) != 1:
            errors.append(f"{where}: unresolved or ambiguous field reference {name!r}")
            return None
        return matches[0]

    def api_ref(name, where):
        if name not in config["apis"]:
            errors.append(f"{where}: unknown API {name!r}")

    def options_for(field):
        if "options" in field:
            return [o["value"] for o in field["options"]]
        return [o["id"] for o in config["vocabularies"].get(field.get("vocabulary"), {}).get("items", [])]

    dependencies = defaultdict(set)
    for section in sections:
        sid = section["id"]
        duplicate_ids([f["id"] for f in section["fields"]], sid)
        local = {f["id"]: (sid, f) for f in section["fields"]}
        condition = section.get("condition", {})
        if condition.get("type") == "checkbox_includes":
            target = resolve(condition["field_id"], sid, local)
            if target and (target[1]["type"] != "checkbox_group" or condition["value"] not in options_for(target[1])):
                errors.append(f"{sid}: condition must select an existing checkbox value")
        if condition.get("type") == "organism_trigger":
            resolve(condition["trigger"], sid, local)
        if "output" in section:
            if section["output"].get("mode") != "collect_object" or not section.get("repeatable"):
                errors.append(f"{sid}: section output requires repeatable collect_object")
        for field in section["fields"]:
            where = f"{sid}/{field['id']}"
            node = (sid, field["id"])
            for key in ("api", "search_api"):
                if key in field:
                    api_ref(field[key], where)
            for name in field.get("api_by_taxon", {}).values():
                api_ref(name, where)
            for names in field.get("api_fallback", {}).values():
                for name in names:
                    api_ref(name, where)
            if "vocabulary" in field and field["vocabulary"] not in config["vocabularies"]:
                errors.append(f"{where}: unknown vocabulary {field['vocabulary']!r}")
            for key in ("depends_on", "dependent_on_field", "update_display_field"):
                if key in field:
                    target = resolve(field[key], where, local)
                    # update_display_field is a write target, not a dependency.
                    if target and key != "update_display_field":
                        dependencies[node].add((target[0], target[1]["id"]))
            for key in ("autofill_from", "autofill_label_to", "orcid_autofill_from", "clear_dependent_fields"):
                for name in field.get(key, []):
                    resolve(name, where, local)
            for action in field.get("on_change", []):
                for name in action["fields"]:
                    resolve(name, where, local)
            visibility = field.get("visible_if")
            if visibility:
                target = resolve(visibility["field"], where, local)
                if target:
                    dependencies[node].add((target[0], target[1]["id"]))
                    if "value" in visibility and target[1]["type"] in ("select", "multi_select", "checkbox_group", "preset_or_search"):
                        if visibility["value"] not in options_for(target[1]):
                            errors.append(f"{where}: visible_if value is not a target option")
            for option in field.get("options", []):
                if "opens_section" in option and option["opens_section"] not in section_ids:
                    errors.append(f"{where}: unknown section {option['opens_section']!r}")
            if "options" in field:
                duplicate_ids([o["value"] for o in field["options"]], where)
            if "min" in field and "max" in field and field["min"] > field["max"]:
                errors.append(f"{where}: min exceeds max")
            if "default" in field:
                if field["type"] == "number":
                    value = field["default"]
                    if isinstance(value, bool) or not isinstance(value, (int, float)):
                        errors.append(f"{where}: number default must be numeric")
                    elif not field.get("min", float('-inf')) <= value <= field.get("max", float('inf')):
                        errors.append(f"{where}: default is outside numeric bounds")
                elif field["type"] == "select" and field["default"] not in options_for(field):
                    errors.append(f"{where}: default is not an option")
            output = field.get("output", {})
            if "obj_key" in output and section.get("output", {}).get("mode") != "collect_object":
                errors.append(f"{where}: obj_key requires a section collect_object output")
            if output.get("mode") == "collect_object":
                errors.append(f"{where}: collect_object belongs on a section")
            if field["type"] in ("text", "textarea", "number"):
                if output.get("tpl", {}).get("valueURI") in ("$value", "$label", "$id"):
                    errors.append(f"{where}: free text must not be copied into valueURI")

    # Visibility/dependency cycles make a field impossible to populate reliably.
    visited, active = set(), set()

    def visit(node):
        if node in active:
            errors.append(f"{'/'.join(node)}: cyclic field dependency")
            return
        if node in visited:
            return
        active.add(node)
        for target in dependencies[node]:
            visit(target)
        active.remove(node)
        visited.add(node)

    for node in list(dependencies):
        visit(node)

    for name, api in config["apis"].items():
        if "depends_on" in api:
            resolve(api["depends_on"], f"apis/{name}")
        for key in ("extra_params_from_context", "path_params_from_context"):
            for value in api.get(key, {}).values():
                if value not in CONTEXT_KEYS:
                    resolve(value, f"apis/{name}/{key}")
        if urlsplit(api["url"]).scheme not in ("http", "https") or not urlsplit(api["url"]).netloc:
            errors.append(f"apis/{name}: URL must use HTTP(S) with a host")
    for name, vocabulary in config["vocabularies"].items():
        duplicate_ids([i["id"] for i in vocabulary["items"]], f"vocabularies/{name}")
        for item in vocabulary["items"]:
            for trigger in item.get("triggers", []):
                if trigger not in VIRTUAL_TRIGGERS:
                    resolve(trigger, f"vocabularies/{name}")
    if not config["meta"]["changelog"].startswith(config["version"] + " - "):
        errors.append("meta/changelog: must start with the configuration version and ' - '")
    for name, locale in (locales or {}).items():
        if not isinstance(locale, dict) or locale.get("version") != config["version"]:
            errors.append(f"i18n/{name}: version must match {config['version']}")
        if not isinstance(locale, dict) or locale.get("locale") != name:
            errors.append(f"i18n/{name}: locale must match filename")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", nargs="?", type=Path, default=ROOT / "fdf_schema.json")
    parser.add_argument("--i18n-dir", type=Path, help="Default: i18n beside the configuration")
    args = parser.parse_args(argv)
    try:
        locale_dir = args.i18n_dir or args.config.parent / "i18n"
        if not locale_dir.is_dir():
            raise ValueError(f"locale directory does not exist: {locale_dir}")
        locales = {p.stem: load_json(p) for p in sorted(locale_dir.glob("*.json"))}
        if not locales:
            raise ValueError(f"no locale sidecars in {locale_dir}")
        errors = validate(load_json(args.config), locales)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"OK: FDF contract, references and {len(locales)} locale version(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
