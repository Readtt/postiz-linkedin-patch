#!/usr/bin/env python3
"""Patch personal LinkedIn OAuth scopes in known Postiz build outputs only."""
from __future__ import annotations

import pathlib
import re
import sys

TARGETS = [
    pathlib.Path(
        "/app/apps/orchestrator/dist/libraries/nestjs-libraries/src/integrations/social/linkedin.provider.js"
    ),
    pathlib.Path(
        "/app/apps/backend/dist/libraries/nestjs-libraries/src/integrations/social/linkedin.provider.js"
    ),
    pathlib.Path(
        "/app/apps/frontend/dist/libraries/nestjs-libraries/src/integrations/social/linkedin.provider.js"
    ),
]

# Match any scopes array that still includes org scopes and/or r_basicprofile
# on the personal LinkedIn provider file.
SCOPES_RE = re.compile(
    r"(scopes\s*=\s*)(\[[^\]]*?(?:w_organization_social|rw_organization_admin|r_basicprofile)[^\]]*?\])",
    re.MULTILINE,
)

# OpenID Sign-In + Share on LinkedIn only (no classic r_basicprofile, no org).
PERSONAL_DQ = '["openid","profile","w_member_social"]'
PERSONAL_SQ = "['openid','profile','w_member_social']"
PERSONAL_TS = "['openid', 'profile', 'w_member_social']"


def normalize(lit: str) -> str:
    if '",' in lit or '"openid"' in lit:
        return PERSONAL_DQ
    if ", " in lit:
        return PERSONAL_TS
    return PERSONAL_SQ


def patch_file(path: pathlib.Path) -> int:
    if not path.is_file():
        print(f"skip missing {path}")
        return 0
    text = path.read_text(encoding="utf-8")
    edits = 0

    def repl(m: re.Match) -> str:
        nonlocal edits
        edits += 1
        return m.group(1) + normalize(m.group(2))

    new_text = SCOPES_RE.sub(repl, text, count=1)
    if edits:
        path.write_text(new_text, encoding="utf-8")
        print(f"patched {path} ({edits} edit(s))")
    else:
        # Already personal-only without r_basicprofile?
        if "w_member_social" in text and "w_organization_social" not in text and "r_basicprofile" not in text:
            print(f"already personal-only {path}")
            return 0
        print(f"no matching scopes in {path}")
    return edits


def main() -> int:
    total = 0
    for path in TARGETS:
        try:
            total += patch_file(path)
        except OSError as e:
            print(f"error on {path}: {e}", file=sys.stderr)
            return 1
    print(f"done: {total} edit(s)")
    if total == 0:
        print("ERROR: no LinkedIn scopes patched", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
