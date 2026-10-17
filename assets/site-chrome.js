/**
 * Shared footer, sticky book/search controls, and booking dialog for all site pages.
 * Designed and built by Paradigm Studio — https://paradigmstudio.net
 */
(function (global) {
    'use strict';

    var BOOKING_URL = 'http://tinyurl.com/y6t4hlo3/';
    var boundMarker = 'data-site-chrome-bound';

    function getSiteRoots() {
        var el = global.document.currentScript;
        if (!el) {
            var scripts = global.document.getElementsByTagName('script');
            for (var i = scripts.length - 1; i >= 0; i--) {
                if (/site-chrome\.js(\?|$)/.test(scripts[i].src || '')) {
                    el = scripts[i];
                    break;
                }
            }
        }
        var customHome = el && el.getAttribute('data-home-root');
        if (customHome != null) {
            var home = customHome;
            if (home && home.charAt(home.length - 1) !== '/') home += '/';
            return { homeRoot: home, assetRoot: home + 'assets/' };
        }
        var src = (el && el.getAttribute('src')) || 'assets/site-chrome.js';
        var assetRoot = src.replace(/[^/]*site-chrome\.js(\?.*)?$/, '');
        var homeRoot = assetRoot.replace(/\/?assets\/?$/, '');
        return { homeRoot: homeRoot, assetRoot: assetRoot };
    }

    function footerHtml(home) {
        return (
            '<div class="footer-content">' +
            '<div class="footer-column footer-column--brand" style="flex: 1.5; padding-right: 50px;">' +
            '<div class="footer-logo">' +
            '<img src="' + home + 'logos/jojoflo_logo-wht.png" alt="JOJO &amp; FLO LONDON">' +
            '</div>' +
            '<p style="color: rgba(255,255,255,0.7); line-height: 1.6; max-width: 300px;">' +
            'Experience the art of hair styling in the heart of London. Where elegance meets expertise.' +
            '</p></div>' +
            '<div class="footer-column">' +
            '<h4 class="footer-heading">Navigation</h4>' +
            '<ul class="footer-links">' +
            '<li><a href="' + home + 'index.html#top">Home</a></li>' +
            '<li><a href="' + home + 'index.html#about-us">About Us</a></li>' +
            '<li><a href="' + home + 'index.html#services">Services</a></li>' +
            '<li><a href="' + home + 'index.html#pricelist">Price List</a></li>' +
            '<li><a href="' + home + 'index.html#gallery">Gallery</a></li>' +
            '</ul></div>' +
            '<div class="footer-column">' +
            '<h4 class="footer-heading">Contact</h4>' +
            '<ul class="footer-links">' +
            '<li><a href="https://maps.google.com/?q=310+Green+Lanes+London+N13+5TT" target="_blank" rel="noopener">310 Green Lanes, London N13 5TT</a></li>' +
            '<li><a href="tel:+442088826400">020 8882 6400</a></li>' +
            '<li><a href="mailto:hello@jojoandflo.com">hello@jojoandflo.com</a></li>' +
            '<li><a href="mailto:recruitingthebest@jojoandflow.com">recruitingthebest@jojoandflow.com</a></li>' +
            '</ul></div>' +
            '<div class="footer-column">' +
            '<h4 class="footer-heading">Hours</h4>' +
            '<ul class="footer-links">' +
            '<li><a href="#">Monday: Closed</a></li>' +
            '<li><a href="#">Tuesday: 10am – 6pm</a></li>' +
            '<li><a href="#">Wednesday: 10am – 6pm</a></li>' +
            '<li><a href="#">Thursday: 10am – 6pm</a></li>' +
            '<li><a href="#">Friday: 10am – 6pm</a></li>' +
            '<li><a href="#">Saturday: 9am – 6pm</a></li>' +
            '<li><a href="#">Sunday: Closed</a></li>' +
            '</ul></div></div>' +
            '<div class="footer-bottom">' +
            '<div>' +
            '<p>&copy; 2025 JOJO &amp; FLO LONDON. All Rights Reserved.</p>' +
            '<p class="footer-legal">' +
            '<a href="' + home + 'terms.html">Terms</a>' +
            '<a href="' + home + 'privacy.html">Privacy</a>' +
            '<a href="' + home + 'offers.html">Offers &amp; Events</a>' +
            '</p>' +
            '<p class="footer-credit" hidden>Website by <a href="https://paradigmstudio.net" target="_blank" rel="noopener">Paradigm Studio</a></p>' +
            '</div>' +
            '<div class="social-icons">' +
            '<a href="#" aria-label="Facebook"><i class="ri-facebook-circle-fill"></i></a>' +
            '<a href="#" aria-label="Instagram"><i class="ri-instagram-fill"></i></a>' +
            '<a href="#" aria-label="Pinterest"><i class="ri-pinterest-fill"></i></a>' +
            '</div></div>'
        );
    }

    function searchPanelHtml() {
        return (
            '<section class="product-search-results" id="productSearchResults" aria-labelledby="productSearchTitle" hidden>' +
            '<div class="product-search-results__inner">' +
            '<div class="product-search-results__head">' +
            '<h2 class="product-search-results__title" id="productSearchTitle">Product search</h2>' +
            '<p class="product-search-results__meta" id="productSearchMeta"></p>' +
            '<button type="button" class="product-search-results__close" id="productSearchClose">Close results</button>' +
            '</div>' +
            '<div class="product-search-results__grid" id="productSearchGrid"></div>' +
            '<p class="product-search-results__empty" id="productSearchEmpty" hidden>No products match your search. Try another keyword.</p>' +
            '</div></section>'
        );
    }

    function stickyControlsHtml() {
        return (
            '<div class="search-btn-sticky" id="searchOpenBtn" role="search" aria-expanded="false" aria-label="Search products">' +
            '<span class="search-btn-sticky__icon"><i class="ri-search-line"></i></span>' +
            '<span class="search-btn-sticky__field">' +
            '<input type="search" class="search-btn-sticky__input" id="heroSearchInput" name="q" placeholder="Search products…" autocomplete="off">' +
            '<button type="button" class="search-btn-sticky__submit" id="heroSearchSubmit">Go</button>' +
            '</span></div>' +
            '<a class="hero-btn book-btn-sticky" id="bookOpenBtn" href="' +
            BOOKING_URL +
            '" target="_blank" rel="noopener noreferrer" aria-expanded="false" aria-label="Book an appointment">' +
            '<span class="book-btn-sticky__text"><span class="book-btn-sticky__word">Book</span><span class="book-btn-sticky__more">An Appointment</span></span>' +
            '</a>'
        );
    }

    function bookDialogHtml() {
        return (
            '<dialog id="bookDialog" class="book-dialog" aria-labelledby="bookDialogTitle">' +
            '<div class="book-dialog__head">' +
            '<h2 id="bookDialogTitle" class="book-dialog__title">Book an appointment</h2>' +
            '<button type="button" class="book-dialog__close" id="bookCloseBtn" aria-label="Close booking">' +
            '<i class="ri-close-line" aria-hidden="true"></i></button></div>' +
            '<div class="book-dialog__body">' +
            '<iframe id="bookFrame" class="book-dialog__frame" title="Book at JoJo &amp; Flo — SalonSynk" loading="lazy" data-src="' +
            BOOKING_URL +
            '"></iframe></div>' +
            '<p class="book-dialog__hint">If the form does not load here (some networks block embeds), ' +
            '<a href="' +
            BOOKING_URL +
            '" target="_blank" rel="noopener noreferrer">open booking in a new tab</a>.</p></dialog>'
        );
    }

    function insertHtmlBeforeFooter(html) {
        var footer = global.document.querySelector('footer');
        var tpl = global.document.createElement('div');
        tpl.innerHTML = html;
        while (tpl.firstChild) {
            if (footer) footer.parentNode.insertBefore(tpl.firstChild, footer);
            else global.document.body.appendChild(tpl.firstChild);
        }
    }

    function appendHtmlToBody(html) {
        var tpl = global.document.createElement('div');
        tpl.innerHTML = html;
        while (tpl.firstChild) global.document.body.appendChild(tpl.firstChild);
    }

    function footerLegalHtml(home) {
        return (
            '<a href="' + home + 'terms.html">Terms</a>' +
            '<a href="' + home + 'privacy.html">Privacy</a>' +
            '<a href="' + home + 'offers.html">Offers &amp; Events</a>'
        );
    }

    function ensureFooter(homeRoot) {
        var footer = global.document.querySelector('footer');
        if (!footer) {
            footer = global.document.createElement('footer');
            global.document.body.appendChild(footer);
        }
        footer.id = 'contact';
        footer.classList.add('site-footer');
        footer.setAttribute('data-studio', 'Paradigm Studio — https://paradigmstudio.net');
        if (!footer.querySelector('.footer-content')) {
            footer.innerHTML = footerHtml(homeRoot);
        }
        ensureFooterLegal(homeRoot);
        ensureFooterCredit();
    }

    function ensureFooterLegal(homeRoot) {
        var bottom = global.document.querySelector('.footer-bottom > div');
        if (!bottom) return;
        var legal = bottom.querySelector('.footer-legal');
        if (!legal) {
            legal = global.document.createElement('p');
            legal.className = 'footer-legal';
            var credit = bottom.querySelector('.footer-credit');
            if (credit) bottom.insertBefore(legal, credit);
            else bottom.appendChild(legal);
        }
        legal.innerHTML = footerLegalHtml(homeRoot);
    }

    function ensureFooterCredit() {
        var bottom = global.document.querySelector('.footer-bottom > div');
        if (!bottom) return;
        var credit = bottom.querySelector('.footer-credit');
        if (!credit) {
            credit = global.document.createElement('p');
            credit.className = 'footer-credit';
            bottom.appendChild(credit);
        }
        credit.hidden = true;
        credit.innerHTML =
            'Website by <a href="https://paradigmstudio.net" target="_blank" rel="noopener">Paradigm Studio</a>';
    }

    function ensureWidgets() {
        if (!global.document.getElementById('productSearchResults')) {
            insertHtmlBeforeFooter(searchPanelHtml());
        }
        if (!global.document.getElementById('searchOpenBtn')) {
            appendHtmlToBody(stickyControlsHtml());
        }
        if (!global.document.getElementById('bookDialog')) {
            appendHtmlToBody(bookDialogHtml());
        }
    }

    function initBooking() {
        var bookOpenBtn = global.document.getElementById('bookOpenBtn');
        if (!bookOpenBtn || bookOpenBtn.getAttribute(boundMarker) === '1') return;
        bookOpenBtn.setAttribute(boundMarker, '1');
        bookOpenBtn.setAttribute('href', BOOKING_URL);
        bookOpenBtn.setAttribute('target', '_blank');
        bookOpenBtn.setAttribute('rel', 'noopener noreferrer');
        bookOpenBtn.removeAttribute('aria-haspopup');
        bookOpenBtn.removeAttribute('aria-controls');

        bookOpenBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            if (!bookOpenBtn.classList.contains('is-expanded')) {
                e.preventDefault();
                bookOpenBtn.classList.add('is-expanded');
                bookOpenBtn.setAttribute('aria-expanded', 'true');
                return;
            }
            if (bookOpenBtn.tagName !== 'A') {
                e.preventDefault();
                global.open(BOOKING_URL, '_blank', 'noopener,noreferrer');
            }
        });
        global.document.addEventListener('click', function (e) {
            if (!bookOpenBtn.classList.contains('is-expanded')) return;
            if (bookOpenBtn.contains(e.target)) return;
            bookOpenBtn.classList.remove('is-expanded');
            bookOpenBtn.setAttribute('aria-expanded', 'false');
        });
    }

    function initSearch(homeRoot) {
        var searchOpenBtn = global.document.getElementById('searchOpenBtn');
        if (!searchOpenBtn || searchOpenBtn.getAttribute(boundMarker) === '1') return;
        searchOpenBtn.setAttribute(boundMarker, '1');

        var heroSearchInput = global.document.getElementById('heroSearchInput');
        var heroSearchSubmit = global.document.getElementById('heroSearchSubmit');
        var productSearchResults = global.document.getElementById('productSearchResults');
        var productSearchGrid = global.document.getElementById('productSearchGrid');
        var productSearchMeta = global.document.getElementById('productSearchMeta');
        var productSearchEmpty = global.document.getElementById('productSearchEmpty');
        var productSearchClose = global.document.getElementById('productSearchClose');
        var shop = global.PaySynkShop;
        var detailPrefix = homeRoot + 'brands/product.html?slug=';

        function hideSearchResults() {
            if (!productSearchResults) return;
            productSearchResults.classList.remove('is-visible');
            productSearchResults.hidden = true;
            if (productSearchGrid) productSearchGrid.innerHTML = '';
        }

        function renderSearchResults() {
            if (!productSearchGrid || !productSearchResults || !shop) return;
            var q = (heroSearchInput && heroSearchInput.value) || '';
            q = q.trim();
            if (!q) {
                hideSearchResults();
                return;
            }
            productSearchResults.hidden = false;
            productSearchResults.classList.add('is-visible');
            productSearchGrid.innerHTML = '';
            if (productSearchEmpty) productSearchEmpty.hidden = true;
            if (productSearchMeta) productSearchMeta.textContent = 'Searching…';
            productSearchResults.scrollIntoView({ behavior: 'smooth', block: 'start' });

            shop.loadCatalog().then(function (catalog) {
                var items = shop.filterProducts(catalog, q);
                productSearchGrid.innerHTML = '';
                if (productSearchMeta) {
                    productSearchMeta.textContent =
                        items.length === 1
                            ? '1 product found for “' + q + '”'
                            : items.length + ' products found for “' + q + '”';
                }
                if (items.length === 0) {
                    if (productSearchEmpty) productSearchEmpty.hidden = false;
                    return;
                }
                if (productSearchEmpty) productSearchEmpty.hidden = true;
                items.forEach(function (p, idx) {
                    if (!p.slug) return;
                    var el = shop.createProductSlot(p.slug);
                    shop.paintProductCard(el, p, {
                        revealIndex: idx,
                        revealBaseDelay: 70,
                        linkToProductPage: true,
                        productDetailHref: detailPrefix
                    });
                    productSearchGrid.appendChild(el);
                });
                shop.revealContainer('#productSearchResults .product-search-results__inner', 0);
            }).catch(function () {
                if (productSearchMeta) {
                    productSearchMeta.textContent = 'Could not load the shop. Please try again.';
                }
                if (productSearchEmpty) productSearchEmpty.hidden = false;
            });
        }

        searchOpenBtn.addEventListener('click', function (e) {
            if (!searchOpenBtn.classList.contains('is-expanded')) {
                searchOpenBtn.classList.add('is-expanded');
                searchOpenBtn.setAttribute('aria-expanded', 'true');
                setTimeout(function () {
                    if (heroSearchInput) heroSearchInput.focus();
                }, 300);
                e.stopPropagation();
            }
        });
        global.document.addEventListener('click', function (e) {
            if (!searchOpenBtn.classList.contains('is-expanded')) return;
            if (searchOpenBtn.contains(e.target)) return;
            if (productSearchResults && !productSearchResults.hidden) return;
            searchOpenBtn.classList.remove('is-expanded');
            searchOpenBtn.setAttribute('aria-expanded', 'false');
        });
        if (heroSearchSubmit) {
            heroSearchSubmit.addEventListener('click', function (e) {
                e.stopPropagation();
                renderSearchResults();
            });
        }
        if (heroSearchInput) {
            heroSearchInput.addEventListener('keydown', function (e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    renderSearchResults();
                }
            });
        }
        if (productSearchClose) {
            productSearchClose.addEventListener('click', function () {
                hideSearchResults();
                if (heroSearchInput) heroSearchInput.value = '';
            });
        }
    }

    function cookieBarHtml(home) {
        return (
            '<div class="cookie-bar" id="cookieBar" hidden role="dialog" aria-label="Cookie consent">' +
            '<p class="cookie-bar__text">We use cookies to run the site and remember your preferences. ' +
            '<a href="' + home + 'privacy.html">Privacy</a></p>' +
            '<div class="cookie-bar__actions">' +
            '<button type="button" class="cookie-bar__btn cookie-bar__btn--ghost" id="cookieReject">Essential only</button>' +
            '<button type="button" class="cookie-bar__btn cookie-bar__btn--solid" id="cookieAccept">Accept</button>' +
            '</div></div>'
        );
    }

    function setCookieConsent(value) {
        try {
            global.localStorage.setItem('jf_cookie_consent', value);
        } catch (e) {}
        var bar = global.document.getElementById('cookieBar');
        if (bar) bar.hidden = true;
        global.document.body.classList.remove('cookie-bar-visible');
    }

    function initCookieBar(homeRoot) {
        var existing = '';
        try {
            existing = global.localStorage.getItem('jf_cookie_consent') || '';
        } catch (e) {}
        if (existing === 'accepted' || existing === 'essential') return;

        if (!global.document.getElementById('cookieBar')) {
            appendHtmlToBody(cookieBarHtml(homeRoot));
        }
        var bar = global.document.getElementById('cookieBar');
        var accept = global.document.getElementById('cookieAccept');
        var reject = global.document.getElementById('cookieReject');
        if (!bar) return;
        bar.hidden = false;
        global.document.body.classList.add('cookie-bar-visible');
        if (accept) accept.addEventListener('click', function () { setCookieConsent('accepted'); });
        if (reject) reject.addEventListener('click', function () { setCookieConsent('essential'); });
    }

    function initSiteChrome() {
        var roots = getSiteRoots();
        ensureFooter(roots.homeRoot);
        ensureWidgets();
        initBooking();
        initSearch(roots.homeRoot);
        initCookieBar(roots.homeRoot);
    }

    global.SiteChrome = { init: initSiteChrome, getSiteRoots: getSiteRoots };

    function boot() {
        initSiteChrome();
    }
    if (global.document.readyState === 'loading') {
        global.document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})(typeof window !== 'undefined' ? window : this);
