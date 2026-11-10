# SPDX-FileCopyrightText: 2026 CNRS
# SPDX-License-Identifier: CECILL-B
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from tools import build_bundle
from tools.validate_schema import ROOT


class BundleTests(unittest.TestCase):
    def test_committed_snapshot_is_validated_and_reproducible(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            for name in ("fdf_schema.json", "schema", "i18n", "tools", "requirements-dev.txt"):
                source = ROOT / name
                if source.is_dir():
                    shutil.copytree(source, repo / name, ignore=shutil.ignore_patterns("__pycache__"))
                else:
                    shutil.copyfile(source, repo / name)

            def git(*args):
                return subprocess.check_output(["git", *args], cwd=repo, stderr=subprocess.DEVNULL)

            git("init")
            git("add", ".")
            git("-c", "user.name=FDF Tests", "-c", "user.email=tests@example.invalid", "commit", "-m", "Fixture")
            commit = git("rev-parse", "HEAD").decode().strip()
            # A dirty working copy cannot misrepresent its bytes as committed.
            (repo / "fdf_schema.json").write_text("invalid working copy")
            with patch.object(build_bundle, "ROOT", repo):
                one = build_bundle.build(commit, repo / "one")
                two = build_bundle.build(commit, repo / "two")
                self.assertEqual(one.read_bytes(), two.read_bytes())
                with self.assertRaises(FileExistsError):
                    build_bundle.build(commit, repo / "one")
                with zipfile.ZipFile(one) as archive:
                    manifest = json.loads(archive.read("manifest.json"))
                    self.assertEqual(manifest["schema_sha"], commit)
                    for name, digest in manifest["files"].items():
                        self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), digest)
                # Invalid committed JSON must fail before creating an artifact.
                git("add", "fdf_schema.json")
                git("-c", "user.name=FDF Tests", "-c", "user.email=tests@example.invalid", "commit", "-m", "Invalid fixture")
                invalid_commit = git("rev-parse", "HEAD").decode().strip()
                with self.assertRaises(subprocess.CalledProcessError):
                    build_bundle.build(invalid_commit, repo / "invalid")
                self.assertFalse((repo / "invalid").exists())

    def test_mutable_ref_is_rejected(self):
        with self.assertRaises(ValueError):
            build_bundle.build("main", Path("unused"))
