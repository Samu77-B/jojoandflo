/**
 * PaySynk product catalog + cart helpers for JOJO & FLO static pages.
 * Products and checkout are managed in PaySynk; this script only loads and displays them.
 */
(function (global) {
    'use strict';

    var STORE = 'jojo-flo-london';
    var PRODUCTS_URL = 'https://www.paysynk.com/api/stores/' + STORE + '/products';
    var CART_EVENT = 'paysynk:cart-updated';

    var catalog = null;
    var currency = 'gbp';

    var BRAND_MATCHERS = {
        kerastase: function (p) {
            var cat = normalizeSearchText(p.category || '');
            var slug = normalizeSearchText(p.slug || '');
            var title = normalizeSearchText(p.title || '');
            if (cat === 'kerastase') return true;
            return slug.indexOf('kerastase') !== -1 || title.indexOf('kerastase') !== -1;
        },
        davines: function (p) {
            if ((p.category || '') === 'Davines') return true;
            return (p.slug || '').indexOf('davines-') === 0;
        },
        'shu-uemura': function (p) {
            if ((p.category || '') === 'Shu Uemura Art of Hair') return true;
            var title = normalizeSearchText(p.title || '');
            return title.indexOf('shu uemura') !== -1;
        }
    };

    function normalizeSearchText(s) {
        return (s || '')
            .toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '');
    }

    function formatMoney(minor, cur) {
        try {
            return new Intl.NumberFormat('en-GB', {
                style: 'currency',
                currency: (cur || currency || 'gbp').toUpperCase()
            }).format((minor || 0) / 100);
        } catch (e) {
            return '£' + ((minor || 0) / 100).toFixed(2);
        }
    }

    function productImage(p) {
        if (p.images && p.images[0]) {
            var u = p.images[0];
            if (u.indexOf('http') === 0) return u;
            if (u.indexOf('/') === 0) return 'https://www.paysynk.com' + u;
            return u;
        }
        if (p.variants && p.variants[0] && p.variants[0].imageUrl) {
            var v = p.variants[0].imageUrl;
            if (v.indexOf('http') === 0) return v;
            if (v.indexOf('/') === 0) return 'https://www.paysynk.com' + v;
            return v;
        }
        return '';
    }

    function loadCatalog() {
        if (catalog) return Promise.resolve(catalog);
        return fetch(PRODUCTS_URL)
            .then(function (res) {
                if (!res.ok) throw new Error('Failed to load products');
                return res.json();
            })
            .then(function (data) {
                catalog = data.products || [];
                if (data.store && data.store.currency) currency = data.store.currency;
                return catalog;
            });
    }

    function enablePreviewCart() {
        try {
            global.localStorage.setItem('paysynk-preview-cart:' + STORE, '1');
        } catch (e) {}
    }

    function addToCart(product) {
        var variant = product.variants && product.variants[0];
        if (!variant) return;
        var key = 'paysynk-cart:' + STORE;
        var items = [];
        try {
            items = JSON.parse(global.localStorage.getItem(key) || '[]');
        } catch (e) {
            items = [];
        }
        var existing = null;
        for (var i = 0; i < items.length; i++) {
            if (items[i].variantId === variant.id) {
                existing = items[i];
                break;
            }
        }
        if (existing) {
            existing.quantity = Math.min(variant.stockQty || 99, (existing.quantity || 0) + 1);
        } else {
            items.push({
                variantId: variant.id,
                productId: product.id,
                title: product.title,
                optionsLabel: '',
                kind: product.kind || 'other',
                priceMinor: variant.priceMinor,
                quantity: 1,
                maxStock: variant.stockQty || 99
            });
        }
        global.localStorage.setItem(key, JSON.stringify(items));
        try {
            global.dispatchEvent(
                new CustomEvent(CART_EVENT, { detail: { store: STORE, items: items } })
            );
        } catch (e) {}
        if (global.PaySynkCart) {
            global.PaySynkCart.refresh();
            global.PaySynkCart.open();
        }
    }

    function paintProductCard(el, p, options) {
        options = options || {};
        var img = productImage(p);
        var variant = (p.variants && p.variants[0]) || {};
        el.style.display = '';
        el.removeAttribute('data-paysynk-missing');
        el.classList.add('product-card');
        el.innerHTML = '';
        if (img) {
            var image = document.createElement('img');
            image.className = 'product-image';
            image.src = img;
            image.alt = p.title || '';
            image.width = 400;
            image.height = 400;
            image.loading = 'lazy';
            el.appendChild(image);
        }
        var info = document.createElement('div');
        info.className = 'product-info';
        var name = document.createElement('h3');
        name.className = 'product-name';
        name.textContent = p.title || '';
        var price = document.createElement('p');
        price.className = 'product-price';
        var priceMinor = variant.priceMinor;
        price.textContent =
            priceMinor > 0 ? formatMoney(priceMinor, currency) : 'Price on enquiry';
        info.appendChild(name);
        info.appendChild(price);
        if (options.linkToProductPage && p.slug) {
            var detailPrefix = options.productDetailHref || 'product.html?slug=';
            var detail = document.createElement('a');
            detail.className = 'product-detail-link';
            detail.href = detailPrefix + encodeURIComponent(p.slug);
            detail.textContent = 'View product';
            info.appendChild(detail);
        }
        var addBtn = document.createElement('button');
        addBtn.type = 'button';
        addBtn.className = 'hero-btn paysynk-add-btn';
        addBtn.textContent = 'Add to cart';
        addBtn.addEventListener('click', function () {
            addToCart(p);
        });
        info.appendChild(addBtn);
        el.appendChild(info);
        if (typeof options.revealIndex === 'number') {
            applyReveal(el, options.revealIndex, options.revealBaseDelay || 80);
        }
    }

    function shouldSkipRevealChild(child) {
        if (!child || child.hidden) return true;
        if (child.classList.contains('retail-grid') || child.classList.contains('paysynk-embeds')) {
            return true;
        }
        var id = child.id || '';
        if (/Loading|Empty|Grid|Embeds/i.test(id)) return true;
        return false;
    }

    function applyReveal(el, index, baseDelay) {
        if (!el) return;
        el.classList.add('reveal-item');
        var delay = (baseDelay || 0) + (index || 0) * 55;
        el.style.setProperty('--reveal-delay', delay + 'ms');
    }

    function revealContainer(container, baseDelay) {
        var root = resolveEl(container);
        if (!root) return;
        var i = 0;
        Array.prototype.forEach.call(root.children, function (child) {
            if (shouldSkipRevealChild(child)) return;
            applyReveal(child, i, baseDelay || 0);
            i += 1;
        });
    }

    function initMainStageReveal(selectors) {
        if (!selectors) {
            selectors = ['.shop-main', '.pdp-main', '.hero-content', '.featured-products'];
        } else if (typeof selectors === 'string') {
            selectors = [selectors];
        }
        selectors.forEach(function (sel) {
            global.document.querySelectorAll(sel).forEach(function (main) {
                revealContainer(main, 0);
            });
        });
    }

    function createProductSlot(slug) {
        var el = document.createElement('div');
        el.className = 'paysynk-product-slot';
        el.setAttribute('data-product-slug', slug);
        return el;
    }

    function resolveEl(target) {
        if (!target) return null;
        if (typeof target === 'string') return global.document.querySelector(target);
        return target;
    }

    function renderFeatured(target, slugs) {
        var grid = resolveEl(target);
        if (!grid) return;
        slugs = slugs || [];
        function render(list) {
            list = list || [];
            grid.innerHTML = '';
            slugs.forEach(function (slug, idx) {
                var el = createProductSlot(slug);
                for (var i = 0; i < list.length; i++) {
                    if (list[i].slug === slug) {
                        paintProductCard(el, list[i], { revealIndex: idx, revealBaseDelay: 90 });
                        break;
                    }
                }
                grid.appendChild(el);
            });
        }
        loadCatalog()
            .then(render)
            .catch(function () {
                render([]);
            });
    }

    function filterByBrand(list, brandKey) {
        var fn = BRAND_MATCHERS[brandKey];
        if (!fn) return list.slice();
        return list.filter(fn);
    }

    function renderBrandGrid(target, brandKey, options) {
        options = options || {};
        var grid = resolveEl(target);
        if (!grid) return;
        var loadingEl = options.loadingEl ? resolveEl(options.loadingEl) : null;
        var emptyEl = options.emptyEl ? resolveEl(options.emptyEl) : null;

        loadCatalog()
            .then(function (list) {
                var items = filterByBrand(list, brandKey);
                if (loadingEl) loadingEl.hidden = true;
                grid.innerHTML = '';
                if (items.length === 0) {
                    if (emptyEl) emptyEl.hidden = false;
                    return;
                }
                if (emptyEl) emptyEl.hidden = true;
                var cardOptions = {
                    linkToProductPage: !!options.linkToProductPage,
                    productDetailHref: options.productDetailHref
                };
                items.forEach(function (p, idx) {
                    if (!p.slug) return;
                    var el = createProductSlot(p.slug);
                    var opts = {
                        linkToProductPage: cardOptions.linkToProductPage,
                        productDetailHref: cardOptions.productDetailHref,
                        revealIndex: idx,
                        revealBaseDelay: 90
                    };
                    paintProductCard(el, p, opts);
                    grid.appendChild(el);
                });
            })
            .catch(function () {
                if (loadingEl) loadingEl.hidden = true;
                if (emptyEl) {
                    emptyEl.textContent =
                        'Could not load the shop. Please refresh or try again later.';
                    emptyEl.hidden = false;
                }
            });
    }

    function renderAllProductsGrid(target, options) {
        options = options || {};
        var grid = resolveEl(target);
        if (!grid) return;
        var loadingEl = options.loadingEl ? resolveEl(options.loadingEl) : null;
        var emptyEl = options.emptyEl ? resolveEl(options.emptyEl) : null;

        loadCatalog()
            .then(function (list) {
                var items = list.slice();
                items.sort(function (a, b) {
                    return (a.title || '').localeCompare(b.title || '', 'en', { sensitivity: 'base' });
                });
                if (loadingEl) loadingEl.hidden = true;
                grid.innerHTML = '';
                if (items.length === 0) {
                    if (emptyEl) emptyEl.hidden = false;
                    return;
                }
                if (emptyEl) emptyEl.hidden = true;
                var cardOptions = {
                    linkToProductPage: !!options.linkToProductPage,
                    productDetailHref: options.productDetailHref
                };
                items.forEach(function (p, idx) {
                    if (!p.slug) return;
                    var el = createProductSlot(p.slug);
                    var opts = {
                        linkToProductPage: cardOptions.linkToProductPage,
                        productDetailHref: cardOptions.productDetailHref,
                        revealIndex: idx,
                        revealBaseDelay: 90
                    };
                    paintProductCard(el, p, opts);
                    grid.appendChild(el);
                });
            })
            .catch(function () {
                if (loadingEl) loadingEl.hidden = true;
                if (emptyEl) {
                    emptyEl.textContent =
                        'Could not load the shop. Please refresh or try again later.';
                    emptyEl.hidden = false;
                }
            });
    }

    function renderSingleProduct(target, slug, options) {
        options = options || {};
        var slot = resolveEl(target);
        if (!slot || !slug) return Promise.reject(new Error('missing target or slug'));
        return loadCatalog().then(function (list) {
            var p = null;
            for (var i = 0; i < list.length; i++) {
                if (list[i].slug === slug) {
                    p = list[i];
                    break;
                }
            }
            if (!p) return null;
            slot.innerHTML = '';
            var el = createProductSlot(slug);
            paintProductCard(el, p, { revealIndex: 0, revealBaseDelay: 40 });
            slot.appendChild(el);
            return p;
        });
    }

    function productHaystack(p) {
        var skuBits = '';
        var variants = p.variants || [];
        for (var i = 0; i < variants.length; i++) {
            skuBits += ' ' + (variants[i].sku || '');
        }
        return normalizeSearchText(
            (p.title || '') +
                ' ' +
                (p.slug || '') +
                ' ' +
                (p.description || '') +
                ' ' +
                (p.category || '') +
                skuBits
        );
    }

    function filterProducts(list, qRaw) {
        var q = normalizeSearchText(qRaw || '').trim();
        if (!q) return [];
        var words = q.split(/\s+/).filter(Boolean);
        return list.filter(function (p) {
            var hay = productHaystack(p);
            return words.every(function (word) {
                return hay.indexOf(word) !== -1;
            });
        });
    }

    function initSiteHeaderMenu() {
        var menuBtn = global.document.getElementById('menuBtn');
        var mainNav = global.document.getElementById('mainNav');
        if (!menuBtn || !mainNav) return;
        var icon = menuBtn.querySelector('i');
        menuBtn.addEventListener('click', function () {
            var open = mainNav.classList.toggle('open');
            menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
            if (icon) {
                icon.classList.toggle('ri-menu-line', !open);
                icon.classList.toggle('ri-close-line', open);
            }
        });
        mainNav.querySelectorAll('a').forEach(function (link) {
            link.addEventListener('click', function () {
                mainNav.classList.remove('open');
                menuBtn.setAttribute('aria-expanded', 'false');
                if (icon) {
                    icon.classList.add('ri-menu-line');
                    icon.classList.remove('ri-close-line');
                }
            });
        });
    }

    function initHeaderCart() {
        function placePaysynkCart() {
            var launcher = global.document.getElementById('paysynk-cart-launcher');
            var slot = global.document.getElementById('headerCart');
            var nativeBtn = global.document.getElementById('headerCartBtn');
            if (launcher && slot && launcher.style.display !== 'none') {
                if (launcher.parentNode !== slot) slot.appendChild(launcher);
                if (nativeBtn) nativeBtn.hidden = true;
                return;
            }
            if (nativeBtn) nativeBtn.hidden = false;
        }
        placePaysynkCart();
        new global.MutationObserver(placePaysynkCart).observe(global.document.body, {
            childList: true
        });
        var headerCartBtn = global.document.getElementById('headerCartBtn');
        if (headerCartBtn) {
            headerCartBtn.addEventListener('click', function () {
                enablePreviewCart();
                if (global.PaySynkCart) {
                    global.PaySynkCart.refresh();
                    global.PaySynkCart.open();
                }
            });
        }
    }

    global.PaySynkShop = {
        STORE: STORE,
        enablePreviewCart: enablePreviewCart,
        loadCatalog: loadCatalog,
        formatMoney: formatMoney,
        paintProductCard: paintProductCard,
        createProductSlot: createProductSlot,
        addToCart: addToCart,
        renderFeatured: renderFeatured,
        renderBrandGrid: renderBrandGrid,
        renderAllProductsGrid: renderAllProductsGrid,
        renderSingleProduct: renderSingleProduct,
        filterProducts: filterProducts,
        filterByBrand: filterByBrand,
        initHeaderCart: initHeaderCart,
        initSiteHeaderMenu: initSiteHeaderMenu,
        initMainStageReveal: initMainStageReveal,
        revealContainer: revealContainer,
        applyReveal: applyReveal
    };
})(typeof window !== 'undefined' ? window : this);
