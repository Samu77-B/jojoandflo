"""
Copy only product images referenced in HTML into assets/site-products/
(mirror paths relative to Products/). Run from repo root:

  python scripts/sync_site_product_images.py

Requires the full Products/ tree to exist locally; Products/ is gitignored.
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = ROOT / "Products"
DEST_ROOT = ROOT / "assets" / "site-products"
HTML_FILES = [
    ROOT / "index.html",
    ROOT / "brands" / "kerastase.html",
    ROOT / "brands" / "davines.html",
    ROOT / "brands" / "shu-uemura.html",
    ROOT / "brands" / "product.html",
]
CATALOG_JS = ROOT / "assets" / "product-catalog.js"

# Matches img src after Products/ or assets/site-products/ (path under brand folders).
SRC_RE = re.compile(r'src="(?:\.\./)?(?:Products/|assets/site-products/)([^"]+)"')
# Brand grids load images from product-catalog.js — keep those assets in sync too.
CATALOG_IMG_RE = re.compile(r'"image"\s*:\s*"assets/site-products/([^"]+)"')
# Omit lifestyle "in hand" shots from the trimmed site bundle (same rule as build_product_catalog).
HAND_RE = re.compile(
    r"(\bhands\b|\bin hands\b|\bin hand\b|\bin_hand\b|product in hand|_in_hand_|/in hands/)",
    re.I,
)


def is_hand_path(rel: str) -> bool:
    return bool(HAND_RE.search(rel.replace("\\", "/")))


def collect_rel_suffixes() -> list[str]:
    seen: set[str] = set()
    for html in HTML_FILES:
        if not html.is_file():
            continue
        text = html.read_text(encoding="utf-8")
        for m in SRC_RE.finditer(text):
            seen.add(m.group(1).replace("\\", "/"))
    if CATALOG_JS.is_file():
        ctext = CATALOG_JS.read_text(encoding="utf-8")
        for m in CATALOG_IMG_RE.finditer(ctext):
            seen.add(m.group(1).replace("\\", "/"))
    return sorted(seen)


def rewrite_html_to_assets() -> None:
    """Point img src at assets/site-products (root vs brands/)."""
    for html in HTML_FILES:
        text = html.read_text(encoding="utf-8")
        new = text
        if html.parent.name == "brands":
            new = new.replace('src="../Products/', 'src="../assets/site-products/')
        else:
            new = new.replace('src="Products/', 'src="assets/site-products/')
        if new != text:
            html.write_text(new, encoding="utf-8")
            print("Updated paths in", html.relative_to(ROOT))


def main() -> int:
    rels = collect_rel_suffixes()
    missing_source: list[str] = []
    for rel in rels:
        if is_hand_path(rel):
            print("SKIP hand-related", rel)
            continue
        dest = DEST_ROOT / Path(rel)
        src = PRODUCTS / Path(rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.is_file():
            shutil.copy2(src, dest)
            print("OK", rel)
        elif dest.is_file():
            print("SKIP (no Products/, dest exists)", rel)
        else:
            missing_source.append(rel)
    if missing_source:
        print("MISSING:", file=sys.stderr)
        for m in missing_source:
            print(" ", m, file=sys.stderr)
        return 1
    rewrite_html_to_assets()
    print(len(rels), "paths; output", DEST_ROOT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
