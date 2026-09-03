#!/usr/bin/env python3
"""
FDF schema sidecar i18n utilities for the fair3r-fdf-schema repository.

Usage:
    python tools/i18n.py template --locale fr
    python tools/i18n.py check --locale fr

Sidecar files live in i18n/<locale>.json. Keys use stable schema ids, e.g.
``sections.title.fields.publication_year.help``. English strings in
fdf_schema.json are the runtime fallback when a translation is missing.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterator
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "fdf_schema.json"
I18N_DIR = ROOT / "i18n"

LOCALIZABLE_KEYS = frozenset({"title", "label", "placeholder", "help_text", "help"})
SKIP_PREFIXES = ("{{", "{%")


def _is_translatable_string(value) -> bool:
    if not isinstance(value, str):
        return False
    stripped = value.strip()
    if not stripped:
        return False
    return not stripped.startswith(SKIP_PREFIXES)


def _safe_key_part(value, fallback: str) -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    if not text:
        return fallback
    if text.startswith(("http://", "https://")):
        text = text.rstrip("/").rsplit("/", 1)[-1]
    text = re.sub(r"[^A-Za-z0-9_-]+", "_", text)
    return text or fallback


def _option_key(option: dict, index: int) -> str:
    for candidate in ("id", "value", "name"):
        if candidate in option:
            return _safe_key_part(option.get(candidate), str(index))
    return str(index)


def iter_schema_i18n_entries(schema: dict) -> Iterator[tuple[str, str]]:
    """Yield (stable_key, english_value) pairs for translatable schema strings."""
    if not isinstance(schema, dict):
        return

    meta = schema.get("meta")
    if isinstance(meta, dict):
        title = meta.get("title")
        if _is_translatable_string(title):
            yield "meta.title", title

    apis = schema.get("apis")
    if isinstance(apis, dict):
        for api_name, api in apis.items():
            if not isinstance(api, dict):
                continue
            label = api.get("label")
            if _is_translatable_string(label):
                yield f"apis.{api_name}.label", label

    vocabularies = schema.get("vocabularies")
    if isinstance(vocabularies, dict):
        for vocab_name, vocab in vocabularies.items():
            if not isinstance(vocab, dict):
                continue
            vocab_label = vocab.get("label")
            if _is_translatable_string(vocab_label):
                yield f"vocabularies.{vocab_name}.label", vocab_label
            for index, item in enumerate(vocab.get("items", []) or []):
                if not isinstance(item, dict):
                    continue
                item_key = _option_key(item, index)
                prefix = f"vocabularies.{vocab_name}.items.{item_key}"
                for prop in ("label", "display"):
                    value = item.get(prop)
                    if _is_translatable_string(value):
                        yield f"{prefix}.{prop}", value

    for section_index, section in enumerate(schema.get("sections", []) or []):
        if not isinstance(section, dict):
            continue
        section_id = _safe_key_part(section.get("id"), str(section_index))
        section_prefix = f"sections.{section_id}"

        title = section.get("title")
        if _is_translatable_string(title):
            yield f"{section_prefix}.title", title

        display_mapping = section.get("display_mapping")
        if isinstance(display_mapping, dict):
            labels = display_mapping.get("labels")
            if isinstance(labels, dict):
                for label_key, label in labels.items():
                    if _is_translatable_string(label):
                        safe_label_key = _safe_key_part(label_key, label_key)
                        yield (
                            f"{section_prefix}.display_mapping.labels.{safe_label_key}",
                            label,
                        )

        for field_index, field in enumerate(section.get("fields", []) or []):
            if not isinstance(field, dict):
                continue
            field_id = _safe_key_part(field.get("id"), str(field_index))
            field_prefix = f"{section_prefix}.fields.{field_id}"
            for key in LOCALIZABLE_KEYS:
                value = field.get(key)
                if _is_translatable_string(value):
                    yield f"{field_prefix}.{key}", value
            for option_index, option in enumerate(field.get("options", []) or []):
                if not isinstance(option, dict):
                    continue
                option_key = _option_key(option, option_index)
                option_label = option.get("label")
                if _is_translatable_string(option_label):
                    yield (
                        f"{field_prefix}.options.{option_key}.label",
                        option_label,
                    )


def load_schema(path: Path = SCHEMA_PATH) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def sidecar_path(locale: str) -> Path:
    return I18N_DIR / f"{locale}.json"


def load_sidecar(locale: str) -> dict:
    path = sidecar_path(locale)
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    strings = payload.get("strings")
    return strings if isinstance(strings, dict) else {}


def build_i18n_sidecar(schema: dict, locale: str, strings: dict | None = None) -> dict:
    entries = dict(iter_schema_i18n_entries(schema))
    merged = {key: "" for key in sorted(entries)}
    existing = load_sidecar(locale)
    for key in merged:
        for source in (existing, strings or {}):
            value = source.get(key)
            if isinstance(value, str) and value.strip():
                merged[key] = value
                break
    return {
        "version": schema.get("version", "unknown"),
        "locale": locale,
        "strings": merged,
    }


def missing_schema_i18n_keys(schema: dict, locale: str) -> list:
    catalog = load_sidecar(locale)
    missing = []
    for key, _english in iter_schema_i18n_entries(schema):
        value = catalog.get(key)
        if not isinstance(value, str) or not value.strip():
            missing.append(key)
    return missing


def cmd_template(locale: str, output: Path | None) -> int:
    schema = load_schema()
    sidecar = build_i18n_sidecar(schema, locale)
    destination = output or sidecar_path(locale)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(sidecar, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(f"Wrote {len(sidecar['strings'])} keys to {destination}")
    return 0


def cmd_check(locale: str) -> int:
    schema = load_schema()
    missing = missing_schema_i18n_keys(schema, locale)
    if not missing:
        print(f"All schema i18n keys are translated for {locale}.")
        return 0
    print(
        f"Missing or empty translations for {locale} ({len(missing)} keys):",
        file=sys.stderr,
    )
    for key in missing:
        print(key, file=sys.stderr)
    return 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    template_parser = subparsers.add_parser(
        "template", help="Write or refresh i18n/<locale>.json with all schema keys."
    )
    template_parser.add_argument("--locale", default="fr")
    template_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Output path (default: i18n/<locale>.json).",
    )

    check_parser = subparsers.add_parser(
        "check", help="Verify i18n/<locale>.json covers the current schema."
    )
    check_parser.add_argument("--locale", default="fr")

    args = parser.parse_args(argv)
    if args.command == "template":
        return cmd_template(args.locale, args.output)
    if args.command == "check":
        return cmd_check(args.locale)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
