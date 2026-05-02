"""
1. Remove packshots under assets/site-products whose path suggests "in hand" / hands imagery.
2. Build assets/product-catalog.js (window.PRODUCT_CATALOG) for brand grids + product detail page.
3. Regenerate brands/*.html listing pages (JS-rendered grid, links to product.html?id=).

Run from repo root:  python scripts/build_product_catalog_and_brands.py
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import sys
from pathlib import Path

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".heic"}

ROOT = Path(__file__).resolve().parents[1]
SITE_PRODUCTS = ROOT / "assets" / "site-products"
CATALOG_JS = ROOT / "assets" / "product-catalog.js"
BRANDS = ROOT / "brands"

# Paths/filenames suggesting hand-held lifestyle shots rather than solo product packshots.
HAND_RE = re.compile(
    r"(\bhands\b|\bin hands\b|\bin hand\b|\bin_hand\b|product in hand|_in_hand_|/in hands/)",
    re.I,
)


def is_hand_path(rel: str) -> bool:
    return bool(HAND_RE.search(rel.replace("\\", "/")))


def brand_from_rel(rel: str) -> tuple[str, str]:
    """Return (brandKey, brandDisplayName)."""
    first = rel.split("/")[0]
    if first == "Davines":
        return "davines", "Davines"
    if first.startswith("K") and "rastase" in first:
        return "kerastase", "Kérastase"
    if first == "Shu Uemura":
        return "shu-uemura", "Shu Uemura Art of Hair"
    return "other", first


def line_title(rel: str) -> str:
    parts = rel.replace("\\", "/").split("/")
    if len(parts) < 3:
        return parts[-1].rsplit(".", 1)[0]
    line = parts[1]
    line = re.sub(r"^\(NEW\)\s*", "", line, flags=re.I).strip()
    return line[:72] if line else parts[-1]


def product_id(rel: str) -> str:
    h = hashlib.sha256(rel.encode("utf-8")).hexdigest()
    return h[:14]


def human_title(brand_name: str, rel: str) -> str:
    line = line_title(rel)
    parts = rel.replace("\\", "/").split("/")
    if brand_name == "Kérastase" and "GLOSS ABSOLU CREME" in rel and len(parts) > 2:
        return f"{brand_name} — {line} — {parts[2]}"
    base = Path(rel).stem
    if len(base) > 40 and base.startswith("KER_"):
        return f"{brand_name} — {line}"
    return f"{brand_name} — {line}"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def kerastase_bucket_key(inner: str) -> tuple[str, str]:
    """
    One visible product card per bucket for Kérastase.
    Travel sizes: keep each distinct filename (SKU packshots).
    Gloss Absolu: one card per immediate subfolder (ECOM vs ECOM X Textures, etc.).
    Other ranges: one card per asset folder.
    """
    parts = inner.replace("\\", "/").split("/")
    if len(parts) < 2:
        return ("misc", inner)
    tail = "/".join(parts[1:])
    if "Travel Sizes" in inner:
        return ("travel", parts[-1])
    if "GLOSS ABSOLU CREME" in inner or (len(parts) > 1 and "GLOSS" in parts[1]):
        sub = parts[2] if len(parts) > 2 else ""
        return ("gloss", sub)
    if "Social Media" in inner:
        return ("social", parts[-1])
    if "Chronologiste" in inner:
        return ("chrono", parts[-1])
    if "Aromes" in inner or "Arom" in parts[1]:
        return ("aromes", parts[-1])
    return ("misc", inner)


def dedupe_catalog_rows(rows: list[dict]) -> list[dict]:
    """Drop duplicate cards: identical file bytes, then Kérastase bucket collapse."""
    def img_path(r: dict) -> Path:
        return ROOT / Path(r["image"])

    # 1) Identical bytes (any brand) — keep smallest file
    by_hash: dict[str, dict] = {}
    for r in rows:
        fp = img_path(r)
        if not fp.is_file():
            continue
        try:
            digest = sha256_file(fp)
            sz = fp.stat().st_size
        except OSError:
            continue
        if digest not in by_hash:
            by_hash[digest] = r
        else:
            prev = img_path(by_hash[digest])
            try:
                if sz < prev.stat().st_size:
                    by_hash[digest] = r
            except OSError:
                pass
    rows = list(by_hash.values())

    # 2) Kérastase — one row per bucket (stops many near-identical Gloss ECOM tiles)
    ker = [r for r in rows if r["brand"] == "kerastase"]
    other = [r for r in rows if r["brand"] != "kerastase"]
    buckets: dict[tuple[str, str], dict] = {}
    for r in ker:
        inner = r["image"].split("assets/site-products/", 1)[1]
        key = kerastase_bucket_key(inner)
        fp = img_path(r)
        try:
            sz = fp.stat().st_size
        except OSError:
            continue
        if key not in buckets:
            buckets[key] = r
        else:
            prev = img_path(buckets[key])
            try:
                if sz < prev.stat().st_size:
                    buckets[key] = r
            except OSError:
                pass
    merged = other + list(buckets.values())
    merged.sort(key=lambda r: (r["brand"], r["title"], r["image"]))
    return merged


def prune_site_products_not_in_catalog(catalog: list[dict]) -> int:
    """Remove image files under assets/site-products that are no longer in the catalog."""
    keep: set[str] = set()
    for r in catalog:
        img = (r.get("image") or "").replace("\\", "/")
        prefix = "assets/site-products/"
        if img.startswith(prefix):
            keep.add(img[len(prefix) :])
    removed = 0
    if not SITE_PRODUCTS.is_dir():
        return 0
    for p in list(SITE_PRODUCTS.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in IMAGE_EXT:
            continue
        rel = p.relative_to(SITE_PRODUCTS).as_posix()
        if rel not in keep:
            p.unlink()
            removed += 1
    # empty dirs
    for d in sorted(SITE_PRODUCTS.rglob("*"), reverse=True):
        if d.is_dir():
            try:
                next(d.iterdir())
            except StopIteration:
                d.rmdir()
    return removed


def delete_hand_assets() -> int:
    removed = 0
    if not SITE_PRODUCTS.is_dir():
        return 0
    for p in list(SITE_PRODUCTS.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(SITE_PRODUCTS).as_posix()
        if is_hand_path(rel):
            p.unlink()
            removed += 1
            print("removed", rel)
    return removed


def build_catalog() -> list[dict]:
    rows: list[dict] = []
    if not SITE_PRODUCTS.is_dir():
        return rows
    for p in sorted(SITE_PRODUCTS.rglob("*")):
        if not p.is_file():
            continue
        rel = "assets/site-products/" + p.relative_to(SITE_PRODUCTS).as_posix()
        inner = p.relative_to(SITE_PRODUCTS).as_posix()
        if is_hand_path(inner):
            continue
        key, bname = brand_from_rel(inner)
        if key == "other":
            continue
        pid = product_id(inner)
        rows.append(
            {
                "id": pid,
                "brand": key,
                "brandName": bname,
                "title": human_title(bname, inner),
                "line": line_title(inner),
                "image": rel,
                "description": (
                    f"Professional {bname} care, available at JOJO & FLO LONDON. "
                    "Our team can advise on suitability for your hair type and how to use it as part of your routine. "
                    "Purchase in salon."
                ),
                "price": "Price on enquiry",
            }
        )
    rows.sort(key=lambda r: (r["brand"], r["title"]))
    rows = dedupe_catalog_rows(rows)
    return rows


def write_catalog_js(catalog: list[dict]) -> None:
    payload = json.dumps(catalog, ensure_ascii=False, indent=2)
    CATALOG_JS.parent.mkdir(parents=True, exist_ok=True)
    CATALOG_JS.write_text(
        "/** Auto-generated by scripts/build_product_catalog_and_brands.py */\n"
        "window.PRODUCT_CATALOG = "
        + payload
        + ";\n",
        encoding="utf-8",
    )
    print("wrote", CATALOG_JS.relative_to(ROOT), len(catalog), "items")


def brand_listing_html(title: str, h1: str, intro: str, brand_key: str) -> str:
    nav = """<nav id="mainNav" aria-label="Primary">
                <ul>
                    <li><a href="../index.html">Home</a></li>
                    <li><a href="../index.html#services">Services</a></li>
                    <li><a href="../index.html#products">Products</a></li>
                    <li><a href="../index.html#brands">Brands</a></li>
                    <li><a href="../index.html#contact">Contact</a></li>
                    <li><a class="nav-cta" href="../index.html#contact">Book</a></li>
                </ul>
            </nav>"""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="icon" href="../logos/jojoflo-fav.png" type="image/png">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/remixicon/4.6.0/remixicon.min.css" rel="stylesheet">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,wght@0,300;0,400;1,300&display=swap" rel="stylesheet">
    <style>
        :root {{
            --font-freight: 'freight-text-pro', 'Source Serif 4', Georgia, serif;
            --primary-bg: #F9F7F2;
            --text-dark: #2C2C2C;
            --text-light: #6E6860;
            --white: #FFFFFF;
            --btn: #c5ad84;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        a {{ text-decoration: none; color: inherit; transition: color 0.2s ease; }}
        ul {{ list-style: none; }}
        body {{ font-family: var(--font-freight); background: var(--primary-bg); color: var(--text-dark); min-height: 100vh; }}
        header {{
            background: #000; color: #fff; padding: 20px 40px 18px; position: sticky; top: 0; z-index: 100;
        }}
        .header-inner {{
            max-width: 1200px; margin: 0 auto; display: flex; flex-direction: column; align-items: center; gap: 18px;
        }}
        .header-top {{ width: 100%; display: flex; justify-content: center; align-items: center; position: relative; }}
        .logo {{ height: 44px; }}
        .logo img {{ height: 100%; width: auto; object-fit: contain; }}
        .menu-icon {{
            display: none; position: absolute; right: 0; background: none; border: none; color: #fff;
            font-size: 24px; cursor: pointer; padding: 6px;
        }}
        nav ul {{ display: flex; flex-wrap: wrap; gap: 28px; justify-content: center; }}
        nav a {{ font-size: 12px; letter-spacing: 1.5px; text-transform: uppercase; color: rgba(255,255,255,0.9); }}
        nav a:hover {{ color: #fff; }}
        .nav-cta {{ color: var(--btn) !important; }}
        .shop-main {{ max-width: 1200px; margin: 0 auto; padding: 48px 24px 100px; }}
        .breadcrumb {{ font-size: 13px; color: var(--text-light); margin-bottom: 32px; }}
        .breadcrumb a {{ text-decoration: underline; text-underline-offset: 3px; }}
        .page-intro {{ margin-bottom: 48px; text-align: center; }}
        .section-tag {{
            display: inline-block; font-size: 12px; letter-spacing: 3px; text-transform: uppercase;
            color: var(--text-light); border-bottom: 1px solid var(--text-light); padding-bottom: 6px; margin-bottom: 20px;
        }}
        h1 {{ font-weight: 300; font-size: clamp(32px, 4vw, 48px); letter-spacing: 1px; margin-bottom: 16px; }}
        .intro-desc {{ max-width: 620px; margin: 0 auto; font-size: 16px; line-height: 1.7; color: var(--text-light); }}
        .retail-grid {{
            display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 28px;
        }}
        a.product-card {{
            display: block; background: var(--white); overflow: hidden;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        a.product-card:hover {{
            transform: translateY(-6px); box-shadow: 0 16px 32px rgba(0,0,0,0.06);
        }}
        .product-image {{
            width: 100%; height: 280px; object-fit: contain; background: #f5f2ed;
        }}
        .product-info {{ padding: 20px; text-align: center; }}
        .product-name {{
            font-weight: 300; font-size: 16px; line-height: 1.35; color: var(--text-dark);
        }}
        .product-hint {{
            font-size: 12px; color: var(--text-light); margin-top: 8px;
            letter-spacing: 0.06em; text-transform: uppercase;
        }}
        footer {{ background: #000; color: #fff; padding: 60px 24px 40px; }}
        .footer-inner {{ max-width: 1200px; margin: 0 auto; text-align: center; }}
        .footer-inner p {{ font-size: 13px; color: rgba(255,255,255,0.5); }}
        .footer-inner a {{ color: rgba(255,255,255,0.7); text-decoration: underline; }}
        @media (max-width: 768px) {{
            header {{ padding: 16px 20px; }}
            .menu-icon {{ display: flex; align-items: center; justify-content: center; }}
            nav {{
                display: flex; flex-direction: column; width: 100%; max-height: 0; overflow: hidden; opacity: 0;
                transition: max-height 0.35s ease, opacity 0.25s ease;
            }}
            nav.open {{ max-height: 400px; opacity: 1; margin-top: 8px; }}
            nav ul {{ flex-direction: column; gap: 16px; align-items: center; }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="header-inner">
            <div class="header-top">
                <a href="../index.html" class="logo">
                    <img src="../logos/jojoflo_logo-wht.png" alt="JOJO & FLO LONDON">
                </a>
                <button class="menu-icon" id="menuBtn" type="button" aria-label="Menu" aria-expanded="false"><i class="ri-menu-line" aria-hidden="true"></i></button>
            </div>
            {nav}
        </div>
    </header>
    <main class="shop-main">
        <nav class="breadcrumb" aria-label="Breadcrumb">
            <a href="../index.html">Home</a> <span aria-hidden="true">/</span> <span>{h1}</span>
        </nav>
        <div class="page-intro">
            <span class="section-tag">Salon retail</span>
            <h1>{h1}</h1>
            <p class="intro-desc">{intro}</p>
        </div>
        <div class="retail-grid" id="productGrid"></div>
    </main>
    <footer>
        <div class="footer-inner">
            <p>&copy; 2025 JOJO &amp; FLO LONDON. Tap a product for details. Purchase in salon.</p>
            <p style="margin-top:12px"><a href="../index.html">Back to home</a></p>
        </div>
    </footer>
    <script src="../assets/product-catalog.js"></script>
    <script>
(function() {{
    var BRAND = {json.dumps(brand_key)};
    var grid = document.getElementById('productGrid');
    var catalog = window.PRODUCT_CATALOG || [];
    function esc(s) {{
        var d = document.createElement('div');
        d.textContent = s;
        return d.innerHTML;
    }}
    catalog.filter(function(p) {{ return p.brand === BRAND; }}).forEach(function(p) {{
        var a = document.createElement('a');
        a.className = 'product-card';
        a.href = 'product.html?id=' + encodeURIComponent(p.id);
        a.innerHTML =
            '<img class="product-image" src="../' + esc(p.image) + '" alt="' + esc(p.title) + '" width="400" height="400" loading="lazy">' +
            '<div class="product-info"><h2 class="product-name">' + esc(p.title) + '</h2>' +
            '<p class="product-hint">' + esc(p.price) + '</p></div>';
        grid.appendChild(a);
    }});
    var menuBtn = document.getElementById('menuBtn');
    var mainNav = document.getElementById('mainNav');
    if (menuBtn && mainNav) {{
        var icon = menuBtn.querySelector('i');
        menuBtn.addEventListener('click', function() {{
            var open = mainNav.classList.toggle('open');
            menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
            if (icon) {{
                icon.classList.toggle('ri-menu-line', !open);
                icon.classList.toggle('ri-close-line', open);
            }}
        }});
        mainNav.querySelectorAll('a').forEach(function(link) {{
            link.addEventListener('click', function() {{
                mainNav.classList.remove('open');
                menuBtn.setAttribute('aria-expanded', 'false');
                if (icon) {{ icon.classList.add('ri-menu-line'); icon.classList.remove('ri-close-line'); }}
            }});
        }});
    }}
}})();
    </script>
</body>
</html>
"""


def write_product_detail_page() -> None:
    path = BRANDS / "product.html"
    path.write_text(
        """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Product | JOJO &amp; FLO LONDON</title>
    <link rel="icon" href="../logos/jojoflo-fav.png" type="image/png">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/remixicon/4.6.0/remixicon.min.css" rel="stylesheet">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,wght@0,300;0,400;1,300&display=swap" rel="stylesheet">
    <style>
        :root {
            --font-freight: 'freight-text-pro', 'Source Serif 4', Georgia, serif;
            --primary-bg: #F9F7F2;
            --text-dark: #2C2C2C;
            --text-light: #6E6860;
            --white: #FFFFFF;
            --btn: #c5ad84;
            --btn-hover: #b39d6f;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        a { text-decoration: none; color: inherit; }
        ul { list-style: none; }
        body { font-family: var(--font-freight); background: var(--primary-bg); color: var(--text-dark); min-height: 100vh; }
        header {
            background: #000; color: #fff; padding: 20px 40px 18px; position: sticky; top: 0; z-index: 100;
        }
        .header-inner { max-width: 1200px; margin: 0 auto; display: flex; flex-direction: column; align-items: center; gap: 18px; }
        .header-top { width: 100%; display: flex; justify-content: center; align-items: center; position: relative; }
        .logo { height: 44px; }
        .logo img { height: 100%; width: auto; object-fit: contain; }
        .menu-icon {
            display: none; position: absolute; right: 0; background: none; border: none; color: #fff;
            font-size: 24px; cursor: pointer; padding: 6px;
        }
        nav ul { display: flex; flex-wrap: wrap; gap: 28px; justify-content: center; }
        nav a { font-size: 12px; letter-spacing: 1.5px; text-transform: uppercase; color: rgba(255,255,255,0.9); }
        .nav-cta { color: var(--btn) !important; }
        .pdp-main { max-width: 1100px; margin: 0 auto; padding: 40px 24px 80px; }
        .breadcrumb { font-size: 13px; color: var(--text-light); margin-bottom: 28px; }
        .breadcrumb a { text-decoration: underline; text-underline-offset: 3px; color: var(--text-light); }
        .breadcrumb a:hover { color: var(--text-dark); }
        .pdp-layout {
            display: grid; grid-template-columns: 1fr 1fr; gap: 48px; align-items: start;
            background: var(--white); padding: 40px; box-shadow: 0 8px 40px rgba(0,0,0,0.04);
        }
        .pdp-media {
            background: #f5f2ed; border-radius: 2px; padding: 24px; text-align: center;
        }
        .pdp-media img { max-width: 100%; height: auto; max-height: 480px; object-fit: contain; }
        .pdp-brand { font-size: 12px; letter-spacing: 2px; text-transform: uppercase; color: var(--text-light); margin-bottom: 10px; }
        .pdp-title { font-weight: 300; font-size: clamp(26px, 3vw, 36px); line-height: 1.2; margin-bottom: 16px; }
        .pdp-price { font-size: 22px; color: #8a7a66; margin-bottom: 24px; }
        .pdp-desc { font-size: 16px; line-height: 1.75; color: var(--text-light); margin-bottom: 28px; }
        .pdp-actions { display: flex; flex-wrap: wrap; gap: 14px; align-items: center; }
        .btn-primary {
            display: inline-block; padding: 14px 28px; background: var(--btn); color: var(--text-dark);
            font-size: 13px; letter-spacing: 1.5px; text-transform: uppercase; border: none; cursor: pointer;
            font-family: var(--font-freight); transition: background 0.2s;
        }
        .btn-primary:hover { background: var(--btn-hover); }
        .btn-ghost {
            display: inline-block; padding: 14px 22px; border: 1px solid #d4cfc4; color: var(--text-light);
            font-size: 12px; letter-spacing: 1px; text-transform: uppercase;
        }
        .btn-ghost[aria-disabled="true"] { opacity: 0.45; cursor: not-allowed; }
        .pdp-note { font-size: 13px; color: var(--text-light); margin-top: 20px; max-width: 36em; }
        .pdp-empty { text-align: center; padding: 80px 24px; color: var(--text-light); }
        footer { background: #000; color: #fff; padding: 48px 24px; text-align: center; }
        footer p { font-size: 13px; color: rgba(255,255,255,0.5); }
        footer a { color: rgba(255,255,255,0.7); text-decoration: underline; }
        @media (max-width: 860px) {
            .pdp-layout { grid-template-columns: 1fr; padding: 28px 20px; }
            .menu-icon { display: flex; align-items: center; justify-content: center; }
            nav { display: flex; flex-direction: column; width: 100%; max-height: 0; overflow: hidden; opacity: 0; transition: max-height 0.35s ease, opacity 0.25s ease; }
            nav.open { max-height: 400px; opacity: 1; margin-top: 8px; }
            nav ul { flex-direction: column; gap: 16px; align-items: center; }
        }
    </style>
</head>
<body>
    <header>
        <div class="header-inner">
            <div class="header-top">
                <a href="../index.html" class="logo"><img src="../logos/jojoflo_logo-wht.png" alt="JOJO & FLO LONDON"></a>
                <button class="menu-icon" id="menuBtn" type="button" aria-label="Menu"><i class="ri-menu-line" aria-hidden="true"></i></button>
            </div>
            <nav id="mainNav" aria-label="Primary">
                <ul>
                    <li><a href="../index.html">Home</a></li>
                    <li><a href="../index.html#products">Products</a></li>
                    <li><a href="../index.html#brands">Brands</a></li>
                    <li><a href="../index.html#contact">Contact</a></li>
                    <li><a class="nav-cta" href="../index.html#contact">Book</a></li>
                </ul>
            </nav>
        </div>
    </header>
    <main class="pdp-main" id="pdpRoot">
        <div class="pdp-empty" id="pdpEmpty" hidden>Product not found. <a href="../index.html#brands">Browse brands</a></div>
        <div id="pdpContent" hidden>
            <nav class="breadcrumb" aria-label="Breadcrumb">
                <a href="../index.html">Home</a> <span aria-hidden="true"> / </span>
                <a href="#" id="bcBrand">Brand</a> <span aria-hidden="true"> / </span>
                <span id="bcTitle">Product</span>
            </nav>
            <div class="pdp-layout">
                <div class="pdp-media">
                    <img id="pdpImg" src="" alt="">
                </div>
                <div class="pdp-detail">
                    <p class="pdp-brand" id="pdpBrand"></p>
                    <h1 class="pdp-title" id="pdpTitle"></h1>
                    <p class="pdp-price" id="pdpPrice"></p>
                    <p class="pdp-desc" id="pdpDesc"></p>
                    <div class="pdp-actions">
                        <a class="btn-primary" id="pdpContact" href="../index.html#contact">Enquire in salon</a>
                        <span class="btn-ghost" aria-disabled="true" title="Purchase in person at the salon">Add to bag</span>
                    </div>
                    <p class="pdp-note">Online checkout is not connected yet — reserve or buy this product by visiting us or calling <a href="tel:+442088826400">020 8882 6400</a>.</p>
                </div>
            </div>
        </div>
    </main>
    <footer>
        <p>&copy; 2025 JOJO &amp; FLO LONDON</p>
        <p style="margin-top:10px"><a href="../index.html">Home</a></p>
    </footer>
    <script src="../assets/product-catalog.js"></script>
    <script>
(function() {
    var params = new URLSearchParams(window.location.search);
    var id = params.get('id');
    var catalog = window.PRODUCT_CATALOG || [];
    var p = catalog.find(function(x) { return x.id === id; });
    var empty = document.getElementById('pdpEmpty');
    var content = document.getElementById('pdpContent');
    if (!p) {
        empty.hidden = false;
        document.title = 'Product not found | JOJO & FLO LONDON';
        return;
    }
    document.title = p.title + ' | JOJO & FLO LONDON';
    var brandHref = p.brand === 'kerastase' ? 'kerastase.html' : p.brand === 'davines' ? 'davines.html' : 'shu-uemura.html';
    document.getElementById('bcBrand').href = brandHref;
    document.getElementById('bcBrand').textContent = p.brandName;
    document.getElementById('bcTitle').textContent = p.line || p.title;
    document.getElementById('pdpBrand').textContent = p.brandName;
    document.getElementById('pdpTitle').textContent = p.title;
    document.getElementById('pdpPrice').textContent = p.price;
    document.getElementById('pdpDesc').textContent = p.description;
    var img = document.getElementById('pdpImg');
    img.src = '../' + p.image;
    img.alt = p.title;
    content.hidden = false;
    var menuBtn = document.getElementById('menuBtn');
    var mainNav = document.getElementById('mainNav');
    if (menuBtn && mainNav) {
        var icon = menuBtn.querySelector('i');
        menuBtn.addEventListener('click', function() {
            var open = mainNav.classList.toggle('open');
            if (icon) { icon.classList.toggle('ri-menu-line', !open); icon.classList.toggle('ri-close-line', open); }
        });
    }
})();
    </script>
</body>
</html>
""",
        encoding="utf-8",
    )
    print("wrote", path.relative_to(ROOT))


def kerastase_featured_pick(catalog: list[dict]) -> dict:
    rows = [r for r in catalog if r.get("brand") == "kerastase"]
    if not rows:
        raise SystemExit("no Kérastase products in catalog for homepage featured")
    rows.sort(key=lambda r: r["image"])
    for r in rows:
        if "PACKSHOT" in r["image"].upper():
            return r
    return rows[0]


def patch_index_featured(catalog: list[dict]) -> None:
    """Ensure homepage featured cards link to product.html?id=… matching the catalog."""
    index = ROOT / "index.html"
    text = index.read_text(encoding="utf-8")

    def pid_for(subpath_contains: str) -> str:
        for r in catalog:
            if subpath_contains in r["image"].replace("\\", "/"):
                return r["id"]
        raise SystemExit("missing catalog match for " + subpath_contains)

    pairs = [
        (
            r'<a href="brands/[^"]+"(\s+class="product-card">\s*<img src="assets/site-products/Shu Uemura/Ultimate Reset/3474636610211_EN_1\.webp")',
            "<a href=\"brands/product.html?id="
            + pid_for("3474636610211_EN_1.webp")
            + r'"\1',
        ),
        (
            r'<a href="brands/[^"]+"(\s+class="product-card">\s*<img src="assets/site-products/Shu Uemura/Izumi Tonic/3474637136512_EN_1\.webp")',
            "<a href=\"brands/product.html?id="
            + pid_for("3474637136512_EN_1.webp")
            + r'"\1',
        ),
        (
            r'<a href="brands/[^"]+"(\s+class="product-card">\s*<img src="assets/site-products/Davines/75111_NOUNOU HAIR MASK 75ML/8004608253402_MAIN\.jpg")',
            "<a href=\"brands/product.html?id="
            + pid_for("8004608253402_MAIN.jpg")
            + r'"\1',
        ),
    ]
    new_text = text
    for pat, repl in pairs:
        new_text2, n = re.subn(pat, repl, new_text, count=1, flags=re.DOTALL)
        if n != 1:
            raise SystemExit("index.html featured patch failed for pattern: " + pat[:80])
        new_text = new_text2

    kf = kerastase_featured_pick(catalog)
    new_text2, n = re.subn(
        r'(<a href="brands/product\.html\?id=)[a-f0-9]+(" class="product-card">\s*<img src=")assets/site-products/Kérastase/[^"]+',
        r"\1" + kf["id"] + r"\2" + kf["image"],
        new_text,
        count=1,
    )
    if n != 1:
        raise SystemExit("index.html: could not patch Kérastase featured card (missing Kérastase img?)")
    new_text = new_text2
    safe_alt = html.escape(kf["title"], quote=True)
    new_text2, n = re.subn(
        r'(<img src="' + re.escape(kf["image"]) + '" alt=")[^"]*(" class="product-image")',
        r"\1" + safe_alt + r"\2",
        new_text,
        count=1,
    )
    if n != 1:
        raise SystemExit("index.html: could not patch Kérastase featured alt")
    new_text = new_text2
    new_text2, n = re.subn(
        r'(<img src="' + re.escape(kf["image"]) + r'"[^>]*>\s*<div class="product-info">\s*<h3 class="product-name">)[^<]*(</h3>)',
        r"\1" + html.escape(kf["title"]) + r"\2",
        new_text,
        count=1,
    )
    if n != 1:
        raise SystemExit("index.html: could not patch Kérastase featured title")
    new_text = new_text2

    index.write_text(new_text, encoding="utf-8")
    print("patched index.html featured links -> product.html")


def main() -> int:
    n = delete_hand_assets()
    print("removed", n, "hand-related files")
    catalog = build_catalog()
    if not catalog:
        print("no products in catalog", file=sys.stderr)
        return 1
    write_catalog_js(catalog)
    n_prune = prune_site_products_not_in_catalog(catalog)
    if n_prune:
        print("removed", n_prune, "image(s) from assets/site-products not in catalog")
    (BRANDS / "kerastase.html").write_text(
        brand_listing_html(
            "Kérastase — Products | JOJO & FLO LONDON",
            "Kérastase",
            "Luxury hair care we use and retail in salon. Tap a product for a full description — purchase in person or by phone.",
            "kerastase",
        ),
        encoding="utf-8",
    )
    (BRANDS / "davines.html").write_text(
        brand_listing_html(
            "Davines — Products | JOJO & FLO LONDON",
            "Davines",
            "Sustainable Italian hair care available in salon. Tap a product for details.",
            "davines",
        ),
        encoding="utf-8",
    )
    (BRANDS / "shu-uemura.html").write_text(
        brand_listing_html(
            "Shu Uemura Art of Hair — Products | JOJO & FLO LONDON",
            "Shu Uemura Art of Hair",
            "Professional Shu Uemura lines in salon. Tap a product for details.",
            "shu-uemura",
        ),
        encoding="utf-8",
    )
    write_product_detail_page()
    patch_index_featured(catalog)
    return 0


if __name__ == "__main__":
    sys.exit(main())
