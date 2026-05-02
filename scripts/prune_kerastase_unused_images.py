"""
Delete Kérastase image files not referenced in assets/product-catalog.js
from:
  - assets/site-products/<Kérastase folder>/
  - Products/<Kérastase folder>/
  - shop/Kerastase/

Preserves HTML, PDF, XML, and other non-image files.

Run from repo root:  python scripts/prune_kerastase_unused_images.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "assets" / "product-catalog.js"
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".heic"}


def load_kerastase_suffixes() -> set[str]:
    text = CATALOG.read_text(encoding="utf-8")
    m = re.search(r"window\.PRODUCT_CATALOG\s*=\s*(\[[\s\S]*\]);", text)
    if not m:
        raise SystemExit("Could not parse product-catalog.js")
    catalog = json.loads(m.group(1))
    suffixes: set[str] = set()
    for row in catalog:
        if row.get("brand") != "kerastase":
            continue
        img = (row.get("image") or "").replace("\\", "/")
        marker = "Kérastase/"
        if marker not in img:
            marker = "K\u00e9rastase/"
        if marker not in img:
            continue
        suffixes.add(img.split(marker, 1)[1])
    if not suffixes:
        raise SystemExit("No Kérastase image suffixes found in catalog")
    return suffixes


def find_kerastase_dirs() -> list[Path]:
    out: list[Path] = []
    sp = ROOT / "assets" / "site-products"
    if sp.is_dir():
        for ch in sp.iterdir():
            if ch.is_dir() and ch.name.endswith("rastase"):
                out.append(ch)
    prod = ROOT / "Products"
    if prod.is_dir():
        for ch in prod.iterdir():
            if ch.is_dir() and ch.name.endswith("rastase"):
                out.append(ch)
    shop_k = ROOT / "shop" / "Kerastase"
    if shop_k.is_dir():
        out.append(shop_k)
    return out


def shop_kerastase_html_image_refs(shop_k: Path) -> set[str]:
    """Relative paths under shop/Kerastase referenced by local HTML (sample shop pages)."""
    refs: set[str] = set()
    if not shop_k.is_dir():
        return refs
    for html in shop_k.rglob("*.html"):
        try:
            text = html.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in re.finditer(r'src="([^"]+\.(?:png|jpe?g|webp|gif))"', text, re.I):
            src = m.group(1).replace("\\", "/")
            if src.startswith(("http://", "https://", "//")):
                continue
            refs.add(src)
    return refs


def prune_dir(brand_root: Path, allowed_suffixes: set[str], extra_keep: set[str]) -> tuple[int, int]:
    """Returns (deleted_count, kept_count)."""
    deleted = 0
    kept = 0
    if not brand_root.is_dir():
        return 0, 0
    for p in sorted(brand_root.rglob("*"), reverse=True):
        if not p.is_file():
            continue
        if p.suffix.lower() not in IMAGE_EXT:
            continue
        rel = p.relative_to(brand_root).as_posix()
        if rel in allowed_suffixes or rel in extra_keep:
            kept += 1
            continue
        p.unlink()
        deleted += 1
    # Remove empty directories (deepest first)
    for p in sorted(brand_root.rglob("*"), reverse=True):
        if p.is_dir():
            try:
                next(p.iterdir())
            except StopIteration:
                p.rmdir()
    return deleted, kept


def main() -> int:
    allowed = load_kerastase_suffixes()
    print(len(allowed), "catalogued Kérastase image path(s)")
    shop_k = ROOT / "shop" / "Kerastase"
    shop_keep = shop_kerastase_html_image_refs(shop_k)
    if shop_keep:
        print("also keeping", len(shop_keep), "image(s) referenced by shop/Kerastase HTML")
    total_del = 0
    total_keep = 0
    for d in find_kerastase_dirs():
        d_rel = d.relative_to(ROOT)
        extra = shop_keep if d.resolve() == shop_k.resolve() else set()
        n_del, n_keep = prune_dir(d, allowed, extra)
        print(f"{d_rel}: removed {n_del}, kept {n_keep}")
        total_del += n_del
        total_keep += n_keep
    print("total removed", total_del, "total kept (this pass)", total_keep)
    return 0


if __name__ == "__main__":
    sys.exit(main())
