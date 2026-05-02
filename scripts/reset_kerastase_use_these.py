"""
Replace Kérastase assets with only Products/Kérastase/Use these/:
- Rebuild assets/site-products/<Kérastase>/ to contain only the Use these/ tree.
- Under Products/Kérastase/, delete every sibling of Use these (files + folders).

Run from repo root:  python scripts/reset_kerastase_use_these.py
Then:  python scripts/build_product_catalog_and_brands.py
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = ROOT / "Products"
SITE = ROOT / "assets" / "site-products"


def find_kerastase_dir(parent: Path) -> Path | None:
    if not parent.is_dir():
        return None
    for ch in parent.iterdir():
        if ch.is_dir() and ch.name.endswith("rastase"):
            return ch
    return None


def main() -> int:
    k_prod = find_kerastase_dir(PRODUCTS)
    if not k_prod:
        print("No Products/.../K*rastase folder found.", file=sys.stderr)
        return 1
    use_src = k_prod / "Use these"
    if not use_src.is_dir():
        print("Missing folder:", use_src, file=sys.stderr)
        return 1

    k_site = SITE / k_prod.name
    if k_site.exists():
        shutil.rmtree(k_site)
    dest_use = k_site / "Use these"
    dest_use.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(use_src, dest_use)
    print("copied", use_src.relative_to(ROOT), "->", dest_use.relative_to(ROOT))

    removed = 0
    for child in list(k_prod.iterdir()):
        if child.name == "Use these":
            continue
        if child.is_file():
            child.unlink()
            removed += 1
        else:
            shutil.rmtree(child)
            removed += 1
    print("removed from Products/K*rastase (except Use these):", removed, "entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
