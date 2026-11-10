# SPDX-FileCopyrightText: 2026 CNRS
# SPDX-License-Identifier: CECILL-B
from copy import deepcopy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.validate_schema import ROOT, load_json, validate


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(ROOT / "fdf_schema.json")
        cls.locales = {p.stem: load_json(p) for p in (ROOT / "i18n").glob("*.json")}

    def test_current_configuration(self):
        self.assertEqual(validate(self.config, self.locales), [])

    def test_invalid_fixtures(self):
        cases = load_json(ROOT / "tests/fixtures/invalid-configurations.json")
        for name, case in cases.items():
            with self.subTest(name=name):
                config = deepcopy(self.config)
                target = config
                for key in case["path"][:-1]:
                    target = target[key]
                target[case["path"][-1]] = case["value"]
                errors = validate(config, self.locales)
                self.assertTrue(errors, f"{name} was accepted")
                self.assertIn(case["error"], "\n".join(errors))

    def test_duplicate_ids_are_scoped_to_sections(self):
        config = deepcopy(self.config)
        config["apis"]["orcid"]["depends_on"] = "nameType"
        self.assertTrue(any("ambiguous" in e for e in validate(config)))

    def test_locale_version_mismatch(self):
        locales = deepcopy(self.locales)
        locales["fr"]["version"] = "3.0.8"
        self.assertTrue(any("version" in e for e in validate(self.config, locales)))

    def test_scientific_semantics(self):
        item = next(i for i in self.config["vocabularies"]["sex_presets"]["items"] if i["id"].endswith("PATO_0001340"))
        self.assertEqual(item["label"], "Hermaphrodite")
        fields = {f["id"]: f for s in self.config["sections"] for f in s["fields"]}
        for name in ("gene_chromosome_location", "allele_identifier_free", "mutationType_display"):
            with self.subTest(field=name):
                template = fields[name]["output"]["tpl"]
                self.assertEqual(template["subject"], "$value")
                self.assertNotIn("valueURI", template)

    def test_cli_rejects_bad_input(self):
        for content in ('{"version":', '{"apis": {}, "apis": {}}'):
            with self.subTest(content=content), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "bad.json"
                path.write_text(content, encoding="utf-8")
                result = subprocess.run(
                    [sys.executable, str(ROOT / "tools/validate_schema.py"), str(path), "--i18n-dir", str(ROOT / "i18n")],
                    capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 1)
                self.assertIn("ERROR:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
