#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 CNRS
# SPDX-License-Identifier: CECILL-B
"""Package a validated, committed FDF snapshot with content hashes.

Usage: python tools/build_bundle.py --ref <full-commit-sha> --output-dir dist
Uncommitted changes are deliberately excluded. Does not publish or deploy.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def build(ref: str, output_dir: Path) -> Path:
    if not re.fullmatch(r"[0-9a-f]{40}", ref):
        raise ValueError("--ref must be a full 40-character commit SHA")
    commit = git("rev-parse", "--verify", ref + "^{commit}").decode().strip()
    names = git("ls-tree", "-r", "--name-only", commit).decode().splitlines()
    required = ["fdf_schema.json", "schema/fdf-contract.schema.json", "tools/validate_schema.py", "tools/i18n.py", "requirements-dev.txt"]
    if any(name not in names for name in required):
        raise ValueError("commit does not contain the configuration and validation contract")
    paths = required + sorted(n for n in names if re.fullmatch(r"i18n/[A-Za-z0-9_-]+\.json", n))
    contents = {name: git("show", f"{commit}:{name}") for name in paths}
    # Validate the exact committed bytes with the validator from that snapshot.
    with tempfile.TemporaryDirectory() as directory:
        snapshot = Path(directory)
        for name, content in contents.items():
            destination = snapshot / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        subprocess.run([sys.executable, str(snapshot / "tools/validate_schema.py")], check=True)
        for name in paths:
            if name.startswith("i18n/"):
                subprocess.run([sys.executable, str(snapshot / "tools/i18n.py"), "check", "--locale", Path(name).stem], check=True)
    config = json.loads(contents["fdf_schema.json"])
    manifest = {
        "schema_id": config["$id"],
        "schema_version": config["version"],
        "schema_sha": commit,
        "schema_sha256": hashlib.sha256(contents["fdf_schema.json"]).hexdigest(),
        "files": {name: hashlib.sha256(data).hexdigest() for name, data in contents.items()},
    }
    contents["manifest.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"fdf-{config['version']}-{commit}.zip"
    # Exclusive creation preserves an existing artifact. Fixed ZIP metadata
    # makes repeated builds of the same commit byte-for-byte reproducible.
    with destination.open("xb") as handle:
        with zipfile.ZipFile(handle, "w", compression=zipfile.ZIP_STORED) as archive:
            for name, data in sorted(contents.items()):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.external_attr = 0o100644 << 16
                archive.writestr(info, data)
    return destination


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args(argv)
    try:
        print(build(args.ref, args.output_dir))
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
