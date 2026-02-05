#!/usr/bin/env python3
"""
Met à jour la version dans build.gradle :  version = 'X.Y.Z'
Sort avec code 1 s'il ne trouve pas la ligne à remplacer.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: update-gradle-version.py <version>")
        return 1

    new_version = sys.argv[1]
    path = Path("build.gradle")

    if not path.exists():
        print("ERROR: build.gradle introuvable")
        return 1

    content = path.read_text(encoding="utf-8")
    updated, n = re.subn(
        r"(?m)^version\s*=\s*['\"][^'\"]+['\"]\s*$",
        f"version = '{new_version}'",
        content,
    )

    if n == 0:
        print("ERROR: Ligne 'version = ...' non trouvée dans build.gradle")
        return 1

    path.write_text(updated, encoding="utf-8")
    print(f"OK: build.gradle version => {new_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
