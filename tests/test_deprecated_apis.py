# SPDX-FileCopyrightText: 2026 CNRS
# SPDX-License-Identifier: CECILL-B
"""An API can be declared deprecated with its replacement; the validator keeps the declaration usable."""
from copy import deepcopy
import unittest

from tools.validate_schema import ROOT, load_json, validate


def deprecate(config, name="ols_doid", replacement="ols_mondo", scheme="DOID", **declaration):
    """Add `name` (a copy of the replacement under another scheme) as a deprecated API."""
    config["apis"][name] = deepcopy(config["apis"][replacement])
    config["apis"][name]["mapper"]["scheme"] = scheme
    config["apis"][name]["deprecated"] = {"since": "2026-11-10", "replaced_by": replacement, "reason": "test", **declaration}
    return config


class DeprecatedApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = load_json(ROOT / "fdf_schema.json")

    def errors(self, config):
        return "\n".join(validate(config))

    def test_a_source_replaced_by_another_is_valid(self):
        self.assertEqual(validate(deprecate(deepcopy(self.base))), [])

    def test_an_endpoint_replaced_behind_the_same_terms_is_valid(self):
        # same scheme as the replacement and as other live APIs: nothing to migrate, only the URL changes
        config = deprecate(deepcopy(self.base), name="ols_efo_old", replacement="ols_efo", scheme="EFO")
        self.assertEqual(validate(config), [])

    def test_the_replacement_must_exist(self):
        config = deprecate(deepcopy(self.base), replaced_by="ols_nothing")
        self.assertIn("replacement API 'ols_nothing' does not exist", self.errors(config))

    def test_an_api_cannot_replace_itself(self):
        config = deprecate(deepcopy(self.base), replaced_by="ols_doid")
        self.assertIn("cannot replace itself", self.errors(config))

    def test_the_replacement_must_be_the_final_one(self):
        config = deprecate(deepcopy(self.base))
        config = deprecate(config, name="ols_doid_older", replacement="ols_mondo", scheme="OLDDO", replaced_by="ols_doid")
        self.assertIn("itself deprecated", self.errors(config))

    def test_no_field_may_still_use_a_deprecated_api(self):
        config = deprecate(deepcopy(self.base))
        disease = next(f for s in config["sections"] for f in s["fields"] if f["id"] == "disease_search")
        disease["api"] = "ols_doid"
        errors = self.errors(config)
        self.assertIn("API 'ols_doid' is deprecated, use 'ols_mondo'", errors)

    def test_a_scheme_shared_with_a_live_api_cannot_be_migrated(self):
        # EFO is also served by live APIs, and the replacement has another scheme: terms could not be told apart
        config = deprecate(deepcopy(self.base), name="ols_efo_old", replacement="ols_mondo", scheme="EFO")
        self.assertIn("stored terms could not be told apart", self.errors(config))

    def test_a_source_change_needs_a_fixed_scheme(self):
        # a scheme chosen per result ("$scheme", like ols_so) cannot identify the stored terms
        config = deprecate(deepcopy(self.base), scheme="$scheme")
        self.assertIn("needs a fixed mapper.scheme", self.errors(config))

    def test_the_declaration_is_checked_by_the_contract(self):
        for name, bad in (("since", "yesterday"), ("replaced_by", ""), ("unknown_key", "x")):
            with self.subTest(bad=name):
                config = deprecate(deepcopy(self.base))
                config["apis"]["ols_doid"]["deprecated"][name] = bad
                self.assertTrue(validate(config))
        config = deprecate(deepcopy(self.base))
        del config["apis"]["ols_doid"]["deprecated"]["since"]
        self.assertTrue(validate(config))


if __name__ == "__main__":
    unittest.main()
