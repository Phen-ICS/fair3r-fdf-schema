#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 CNRS
# SPDX-License-Identifier: CECILL-B
"""
Generate a Mermaid diagram of the FDF form structure from fdf_schema.json.

Usage:
    python tools/generate_diagram.py

Reads every section and field in the schema and renders one Mermaid
flowchart: each section is a colored subgraph (using its own
`display_mapping.accent_color`), each field is a node labeled with its
id, type, and ontology/vocabulary when known, external APIs are their own
nodes with edges from the fields that call them, and `depends_on` /
`dependent_on_field` / `update_display_field` relations are drawn as
dashed edges between fields. Written to docs/schema-diagram.md so GitHub
renders it inline.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "fdf_schema.json"
OUTPUT_PATH = ROOT / "docs" / "schema-diagram.md"

FALLBACK_ACCENT = "#64748b"


def slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", text)


def escape_label(text: str) -> str:
    return str(text).replace('"', "'")


def collect_field_apis(field: dict) -> list[str]:
    apis: list[str] = []
    for key in ("api", "search_api"):
        if field.get(key):
            apis.append(field[key])
    for key in ("api_by_taxon", "api_fallback"):
        value = field.get(key)
        if isinstance(value, dict):
            for v in value.values():
                if isinstance(v, list):
                    apis.extend(v)
                elif v:
                    apis.append(v)
    seen: list[str] = []
    for a in apis:
        if a not in seen:
            seen.append(a)
    return seen


def field_scheme(field: dict, apis: dict, field_apis: list[str]) -> str | None:
    tpl = ((field.get("output") or {}).get("tpl")) or {}
    scheme = tpl.get("subjectScheme")
    if isinstance(scheme, str) and not scheme.startswith("$"):
        return scheme
    # Dynamic ("$scheme") or absent: fall back to the scheme(s) declared by
    # the API mapper(s) this field actually calls.
    schemes = []
    for api_name in field_apis:
        mapper_scheme = (apis.get(api_name, {}).get("mapper") or {}).get("scheme")
        if mapper_scheme and mapper_scheme not in schemes:
            schemes.append(mapper_scheme)
    return "/".join(schemes) if schemes else None


def build_diagram(schema: dict) -> str:
    apis = schema.get("apis", {})
    lines = ["flowchart TB"]
    lines.append("    classDef apiField fill:#e0f2fe,stroke:#0369a1,stroke-width:1px;")
    lines.append("    classDef plainField fill:#f8fafc,stroke:#94a3b8,stroke-width:1px;")

    field_node_id: dict[tuple[str, str], str] = {}
    field_deps: list[tuple[str, str, str]] = []  # (from_field_key, to_field_key, label)
    chain_order: list[str] = []  # every node id, in emission order

    for section in schema.get("sections", []):
        sid = slug(section["id"])
        title = escape_label(section.get("title", section["id"]))
        dm = section.get("display_mapping")
        accent = dm.get("accent_color") if isinstance(dm, dict) else None
        accent = accent or FALLBACK_ACCENT

        lines.append(f'    subgraph sec_{sid}["{title}"]')
        lines.append(f"        direction TB")
        for field in section.get("fields", []):
            fkey = (section["id"], field["id"])
            fid = "f_" + slug(f'{section["id"]}_{field["id"]}')
            field_node_id[fkey] = fid

            ftype = field.get("type", "?")
            fapis = collect_field_apis(field)
            scheme = field_scheme(field, apis, fapis)
            vocab = field.get("vocabulary")

            label_parts = [field["id"], f"type: {ftype}"]
            if fapis:
                api_labels = [apis.get(a, {}).get("label", a) for a in fapis]
                label_parts.append(f"api: {' / '.join(api_labels)}")
            if scheme:
                label_parts.append(f"ontology: {scheme}")
            if vocab:
                label_parts.append(f"vocab: {vocab}")
            label = "<br/>".join(escape_label(p) for p in label_parts)

            css_class = "apiField" if fapis else "plainField"
            lines.append(f'        {fid}("{label}"):::{css_class}')
            chain_order.append(fid)

            depends_on = field.get("depends_on")
            if depends_on:
                # Edge points from the prerequisite to the dependent field
                # (not the other way around) so it runs the same direction
                # as the field declaration order / layout chain below.
                field_deps.append((section["id"], depends_on, section["id"], field["id"], "enables"))
            dependent_on = field.get("dependent_on_field")
            if dependent_on:
                field_deps.append((section["id"], dependent_on, section["id"], field["id"], "triggers"))
            update_target = field.get("update_display_field")
            if update_target:
                field_deps.append((section["id"], field["id"], section["id"], update_target, "pushes to"))

        lines.append(f"        style sec_{sid} fill:{accent}1a,stroke:{accent},stroke-width:2px")
        lines.append("    end")

    # Invisible edges chaining every single node in emission order force
    # Mermaid's layout to stack the whole diagram top-to-bottom, one rank
    # after another, instead of spreading same-rank nodes/subgraphs out
    # sideways when there aren't enough real edges between them to imply an
    # order on their own. depends_on edges above already run the same
    # direction as this chain, so the two sets of constraints agree instead
    # of fighting each other.
    for prev_id, next_id in zip(chain_order, chain_order[1:]):
        lines.append(f"    {prev_id} ~~~ {next_id}")

    for src_sec, src_field, dst_sec, dst_field, rel_label in field_deps:
        src_id = field_node_id.get((src_sec, src_field))
        dst_id = field_node_id.get((dst_sec, dst_field))
        if src_id and dst_id:
            lines.append(f'    {src_id} -.->|{rel_label}| {dst_id}')

    return "\n".join(lines)


def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text())
    diagram = build_diagram(schema)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    content = (
        "# FDF schema diagram\n\n"
        "Auto-generated from `fdf_schema.json` by `tools/generate_diagram.py`. "
        "Do not edit by hand — regenerate instead.\n\n"
        f"```mermaid\n{diagram}\n```\n"
    )
    OUTPUT_PATH.write_text(content)
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
