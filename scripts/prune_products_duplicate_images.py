"""
Remove duplicate image *files* under Products/ (same bytes as another file).

- Paths listed in assets/product-catalog.js (as assets/site-products/...) are
  always kept under the matching Products/<same relative path>.
- For any other identical-hash group, keep one file (lexicographically first path)
  and delete the rest.

Does not modify assets/site-products/ or shop/.

Run from repo root:  python scripts/prune_products_duplicate_images.py
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = ROOT / "Products"
CATALOG = ROOT / "assets" / "product-catalog.js"
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".heic"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_required_products_paths() -> set[str]:
    text = CATALOG.read_text(encoding="utf-8")
    m = re.search(r"window\.PRODUCT_CATALOG\s*=\s*(\[[\s\S]*\]);", text)
    if not m:
        raise SystemExit("Could not parse product-catalog.js")
    catalog = json.loads(m.group(1))
    req: set[str] = set()
    for row in catalog:
        img = (row.get("image") or "").replace("\\", "/")
        prefix = "assets/site-products/"
        if not img.startswith(prefix):
            continue
        req.add(img[len(prefix) :])
    return req


def main() -> int:
    if not PRODUCTS.is_dir():
        print("No Products/ folder — nothing to do.")
        return 0
    required = load_required_products_paths()
    print(len(required), "paths required by product catalog")

    by_hash: dict[str, list[str]] = defaultdict(list)
    scanned = 0
    for p in PRODUCTS.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in IMAGE_EXT:
            continue
        rel = p.relative_to(PRODUCTS).as_posix()
        try:
            digest = sha256_file(p)
        except OSError as e:
            print("skip (read error)", rel, e, file=sys.stderr)
            continue
        by_hash[digest].append(rel)
        scanned += 1
        if scanned % 800 == 0:
            print("  hashed", scanned, "files...")

    print("scanned", scanned, "images in Products/")

    to_delete: list[str] = []
    for digest, paths in by_hash.items():
        if len(paths) < 2:
            continue
        paths_sorted = sorted(paths)
        in_req = [p for p in paths_sorted if p in required]
        if in_req:
            keep = set(in_req)
        else:
            keep = {paths_sorted[0]}
        for p in paths_sorted:
            if p not in keep:
                to_delete.append(p)

    print("duplicate files to remove:", len(to_delete))
    for rel in to_delete:
        fp = PRODUCTS / rel
        try:
            fp.unlink()
        except OSError as e:
            print("unlink failed", rel, e, file=sys.stderr)

    # Remove empty directories bottom-up
    removed_dirs = 0
    for d in sorted(PRODUCTS.rglob("*"), reverse=True):
        if d.is_dir():
            try:
                next(d.iterdir())
            except StopIteration:
                d.rmdir()
                removed_dirs += 1
    print("removed empty dirs:", removed_dirs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
