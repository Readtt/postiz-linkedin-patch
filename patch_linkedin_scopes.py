#!/usr/bin/env python3
"""Replace org scopes on personal LinkedIn provider only (not linkedin-page)."""
from __future__ import annotations

import pathlib
import re
import sys

ROOTS = [pathlib.Path("/app"), pathlib.Path("/www")]
EXTS = {".js", ".mjs", ".cjs", ".map"}

# Common compiled variants of the scopes array.
ORG_SCOPES = [
    "rw_organization_admin",
    "w_organization_social",
    "r_organization_social",
]

PERSONAL_SCOPES_TS = (
    "['openid', 'profile', 'w_member_social', 'r_basicprofile']"
)
PERSONAL_SCOPES_JS_DQ = (
    '["openid","profile","w_member_social","r_basicprofile"]'
)
PERSONAL_SCOPES_JS_SQ = (
    "['openid','profile','w_member_social','r_basicprofile']"
)

# Match a scopes assignment that includes org scopes.
SCOPES_RE = re.compile(
    r"(scopes\s*=\s*)(\[[^\]]*(?:w_organization_social|rw_organization_admin)[^\]]*\])",
    re.MULTILINE,
)

# Identify personal linkedin vs page: prefer edits near identifier 'linkedin'
# that are NOT 'linkedin-page'.
IDENT_RE = re.compile(
    r"""identifier\s*=\s*['\"]linkedin['\"]""",
)
PAGE_IDENT_RE = re.compile(
    r"""identifier\s*=\s*['\"]linkedin-page['\"]""",
)


def normalize_scopes_literal(lit: str) -> str:
    """Pick replacement style to match the original literal."""
    if '"' in lit and "'" not in lit.replace("\\'", ""):
        return PERSONAL_SCOPES_JS_DQ
    if "'," in lit or "'openid'" in lit:
        return PERSONAL_SCOPES_JS_SQ if "'," in lit.replace(", ", ",") or "'openid'" in lit else PERSONAL_SCOPES_TS
    if ", " in lit:
        return PERSONAL_SCOPES_TS
    return PERSONAL_SCOPES_JS_DQ


def should_skip_path(p: pathlib.Path) -> bool:
    parts = set(p.parts)
    if "node_modules" in parts and "dist" not in parts and ".next" not in parts:
        # Allow scanning built app dirs; skip pure deps noise when huge
        if any(x in parts for x in ("pnpm", ".pnpm")):
            return True
    return False


def patch_text(text: str) -> tuple[str, int]:
    """Patch personal LinkedIn scopes; leave linkedin-page alone when possible."""
    if "w_organization_social" not in text and "rw_organization_admin" not in text:
        return text, 0

    # Split by linkedin-page identifier markers to avoid editing page provider
    # when both live in one file.
    if PAGE_IDENT_RE.search(text) and IDENT_RE.search(text):
        # Process segments: edit only segments that claim identifier linkedin
        # without linkedin-page immediately governing them.
        parts = re.split(
            r"(identifier\s*=\s*['\"]linkedin(?:-page)?['\"])",
            text,
        )
        out = []
        edits = 0
        mode = None  # 'personal' | 'page' | None
        for part in parts:
            if part == "identifier = 'linkedin'" or part == 'identifier = "linkedin"' or part == "identifier='linkedin'" or part == 'identifier="linkedin"':
                mode = "personal"
                out.append(part)
                continue
            if "linkedin-page" in part and part.strip().startswith("identifier"):
                mode = "page"
                out.append(part)
                continue
            if mode == "personal":
                def repl(m: re.Match) -> str:
                    nonlocal edits
                    edits += 1
                    return m.group(1) + normalize_scopes_literal(m.group(2))

                out.append(SCOPES_RE.sub(repl, part, count=1))
            else:
                out.append(part)
        return "".join(out), edits

    # Single-provider file or only personal
    if PAGE_IDENT_RE.search(text) and not IDENT_RE.search(text):
        return text, 0

    edits = 0

    def repl(m: re.Match) -> str:
        nonlocal edits
        edits += 1
        return m.group(1) + normalize_scopes_literal(m.group(2))

    new_text = SCOPES_RE.sub(repl, text, count=1)
    return new_text, edits


def main() -> int:
    changed_files = 0
    total_edits = 0
    seen = set()

    for root in ROOTS:
        if not root.exists():
            continue
        try:
            walker = root.rglob("*")
        except PermissionError as e:
            print(f"skip root {root}: {e}")
            continue
        for p in walker:
            try:
                is_file = p.is_file()
            except PermissionError:
                continue
            if not is_file:
                continue
            if p.suffix not in EXTS and p.name not in {"main.js", "index.js"}:
                if p.suffix not in EXTS:
                    continue
            if should_skip_path(p):
                continue
            try:
                real = p.resolve()
            except Exception:
                continue
            if real in seen:
                continue
            seen.add(real)
            try:
                raw = p.read_bytes()
            except Exception:
                continue
            # Skip huge binaries
            if len(raw) > 20_000_000:
                continue
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                continue
            new_text, edits = patch_text(text)
            if edits:
                p.write_text(new_text, encoding="utf-8")
                changed_files += 1
                total_edits += edits
                print(f"patched {p} ({edits} edit(s))")

    print(f"done: {changed_files} file(s), {total_edits} edit(s)")
    if total_edits == 0:
        print("WARNING: no LinkedIn org scopes found to patch", file=sys.stderr)
        # Don't fail the build hard — surface warning; deploy still boots
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
