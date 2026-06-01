"""Discovery: capture filter and cart selectors on the Education QA storefront.

Run via: python discover_filters.py
Writes findings to mcp-selectors/discovery_filters.json so they can be reviewed
and folded into mcp-selectors/locators.json by the agent.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
URL = "https://storefront:storefront@education-qa.scholastic.ca/en/home"
EMAIL = "qauto@myyahoo.com"
PASSWORD = "passw0rd"

OUT = ROOT / "mcp-selectors" / "discovery_filters.json"

EXPECTED_FILTERS = [
    "Curriculum",
    "Grade",
    "Language",
    "GRL: F&P",
    "GRL: DRA",
    "Program",
    "Subject",
    "Price",
    "Product Type",
    "Book Type",
]


def safe(call, default=None):
    try:
        return call()
    except Exception as exc:
        return {"_error": str(exc)} if default is None else default


def main():
    findings = {"steps": []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=60)
        context = browser.new_context(
            viewport={"width": 1600, "height": 1000},
            http_credentials={"username": "storefront", "password": "storefront"},
            ignore_https_errors=True,
        )
        page = context.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        # CMP banner if present
        cmp = page.locator('iframe[id^="sp_message_iframe_"]').all()
        if cmp:
            try:
                frame = cmp[0].content_frame
                if frame is not None:
                    btn = frame.locator('button[title="Accept All Cookies"]').first
                    btn.wait_for(state="visible", timeout=5000)
                    btn.click()
                    page.wait_for_timeout(500)
                    findings["steps"].append({"step": "cmp_accept", "ok": True})
            except Exception as exc:
                findings["steps"].append({"step": "cmp_accept", "ok": False, "error": str(exc)})

        # Click Sign In via the Educator Sign In link, falling back across known DOM variants.
        sign_in_clicked = False
        for sel in [
            'a.signModal[aria-label="Login to your account"]',
            'a.signModal:has-text("Educator Sign In")',
            'a.signModal:has-text("Sign In")',
            'a#myaccount',
        ]:
            loc = page.locator(sel)
            if loc.count() == 0:
                continue
            for i in range(loc.count()):
                cand = loc.nth(i)
                try:
                    if cand.is_visible():
                        cand.click()
                        sign_in_clicked = True
                        break
                except Exception:
                    continue
            if sign_in_clicked:
                findings["steps"].append({"step": "sign_in_link_clicked", "selector": sel})
                break
        assert sign_in_clicked, "Could not click any visible sign-in link"

        # Wait for whichever login form variant appears
        page.wait_for_function(
            "() => !!document.querySelector('form#dwfrm_login, form#loginForm, form[name=\"login-form\"]')",
            timeout=30000,
        )
        login_state = page.evaluate(
            """() => {
                const dwf = document.querySelector('form#dwfrm_login');
                const lf = document.querySelector('form#loginForm');
                return {
                    dwfrm_login: !!dwf,
                    loginForm: !!lf,
                    dw_username_count: document.querySelectorAll('form#dwfrm_login input[name^="dwfrm_login_username"]').length,
                    dw_password_count: document.querySelectorAll('form#dwfrm_login input[type="password"]').length,
                    dw_submit_count: document.querySelectorAll('form#dwfrm_login button[name="dwfrm_login_login"]').length,
                    lf_email_count: document.querySelectorAll('input#login-form-email').length,
                    lf_password_count: document.querySelectorAll('input#login-form-password').length,
                    lf_submit_count: document.querySelectorAll('button#loginFormSubmitCta').length,
                };
            }"""
        )
        findings["steps"].append({"step": "login_form_state", "info": login_state})

        if login_state.get("dwfrm_login"):
            page.locator('form#dwfrm_login input[name^="dwfrm_login_username"]').first.fill(EMAIL)
            page.locator('form#dwfrm_login input[type="password"]').first.fill(PASSWORD)
            page.locator('form#dwfrm_login button[name="dwfrm_login_login"]').first.click()
        else:
            page.locator('input#login-form-email').first.fill(EMAIL)
            page.locator('input#login-form-password').first.fill(PASSWORD)
            page.locator('button#loginFormSubmitCta').first.click()
        try:
            page.wait_for_load_state("networkidle", timeout=30000)
        except Exception:
            pass
        # Wait for any logged-in marker; if none found in 30s, just probe and continue
        page.wait_for_timeout(3000)
        try:
            page.wait_for_function(
                """() => !!document.querySelector('a.user-logout, a#myaccount, .user-logout, .user-firstname, [data-element-linkname*="Logout"]')""",
                timeout=30000,
            )
        except Exception:
            pass
        post_login = page.evaluate(
            """() => ({
                user_logout: document.querySelectorAll('a.user-logout').length,
                myaccount: document.querySelectorAll('a#myaccount').length,
                user_firstname: document.querySelectorAll('.user-firstname').length,
                signModal: document.querySelectorAll('a.signModal').length,
                welcome_text: Array.from(document.querySelectorAll('button, a, span')).filter(el => /welcome/i.test((el.textContent||''))).slice(0,3).map(el=>({tag:el.tagName, classes:el.className, text:(el.textContent||'').trim().slice(0,60)})),
                page_url: location.href,
            })"""
        )
        findings["steps"].append({"step": "post_login_state", "info": post_login})
        findings["steps"].append({"step": "logged_in", "url": page.url})

        # Probe search form selectors first
        search_probe = page.evaluate(
            """() => {
                const out = {forms: [], submits: [], inputs: []};
                const forms = document.querySelectorAll('form[role="search"], form[name="simpleSearch"]');
                for (const f of forms) {
                    out.forms.push({id: f.id, name: f.getAttribute('name'), role: f.getAttribute('role'), action: f.getAttribute('action'), classes: f.className});
                    for (const inp of f.querySelectorAll('input')) {
                        out.inputs.push({id: inp.id, name: inp.name, type: inp.type, classes: inp.className, placeholder: inp.placeholder});
                    }
                    for (const btn of f.querySelectorAll('button, [type="submit"], svg, [role="button"]')) {
                        out.submits.push({tag: btn.tagName, id: btn.id, name: btn.getAttribute && btn.getAttribute('name'), aria: btn.getAttribute && btn.getAttribute('aria-label'), classes: btn.className.toString ? btn.className.toString() : '', text: (btn.textContent || '').trim().slice(0,40)});
                    }
                }
                return out;
            }"""
        )
        findings["steps"].append({"step": "search_form_probe", "info": search_probe})

        # Click search icon to view all items (try across known variants)
        clicked_search = None
        for sel in [
            'form[role="search"] button[name="search-button"]',
            'form[role="search"] button[type="submit"]',
            'form[role="search"] svg[name="search-button"]',
            'form[role="search"] [aria-label="Submit search keywords"]',
            'form[name="simpleSearch"] button[type="submit"]',
            'form[name="simpleSearch"] button[name="search-button"]',
            'button.global-search-button',
            '.search-button',
            'header [aria-label*="Search" i]',
        ]:
            try:
                loc = page.locator(sel)
                if loc.count() > 0:
                    for i in range(loc.count()):
                        c = loc.nth(i)
                        try:
                            if c.is_visible():
                                c.click()
                                clicked_search = sel
                                break
                        except Exception:
                            continue
                if clicked_search:
                    break
            except Exception:
                continue
        # Fallback: submit the visible search form by pressing Enter on the input
        if not clicked_search:
            for sel in [
                'form[role="search"] input.search-field',
                'form[name="simpleSearch"] input.search-field',
                'input.search-field',
            ]:
                loc = page.locator(sel)
                if loc.count() > 0:
                    for i in range(loc.count()):
                        c = loc.nth(i)
                        try:
                            if c.is_visible():
                                c.click()
                                c.press("Enter")
                                clicked_search = f"{sel} (Enter)"
                                break
                        except Exception:
                            continue
                if clicked_search:
                    break
        findings["steps"].append({"step": "search_clicked", "selector": clicked_search})
        try:
            page.wait_for_url("**/search*", timeout=15000)
        except Exception:
            pass
        try:
            page.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            pass
        findings["steps"].append({"step": "search_results", "url": page.url, "title": page.title()})

        # Probe Filter By: label and refinement bar
        filter_probe = {}
        for sel in [
            ".refinement-bar",
            "aside.refinement-bar",
            ".refinement-bar h3",
            ".refinement-bar h4",
            ".refinement-bar .secondary-bar",
            ".refinements",
            'button:has-text("Clear All")',
            "button.reset",
            "a.reset",
            ".refinement-header",
        ]:
            filter_probe[sel] = page.locator(sel).count()
        findings["steps"].append({"step": "filter_probe_counts", "counts": filter_probe})

        # Find the explicit "Filter By:" label via JS (case-insensitive)
        try:
            label_info = page.evaluate(
                """() => {
                    const all = document.querySelectorAll('.refinement-bar h3, .refinement-bar .secondary-bar, .refinement-bar .filter-label, .refinement-bar h2');
                    const out = [];
                    for (const el of all) {
                        const t = (el.textContent || '').trim();
                        if (/filter\\s*by/i.test(t)) {
                            out.push({tag: el.tagName, classes: el.className, text: t.slice(0,80)});
                        }
                    }
                    // Fallback: scan whole .refinement-bar
                    const bar = document.querySelector('.refinement-bar');
                    let barText = '';
                    if (bar) barText = (bar.textContent || '').trim().slice(0, 200);
                    return {found: out, barText};
                }"""
            )
            findings["steps"].append({"step": "filter_label_info", "info": label_info})
        except Exception as exc:
            findings["steps"].append({"step": "filter_label_info", "error": str(exc)})

        # Find each refinement section by aria-label / data class
        sections_probe = page.evaluate(
            """() => {
                const refs = document.querySelectorAll('.refinement');
                return Array.from(refs).map(r => {
                    const h4 = r.querySelector('h4.refinement-key');
                    const header = r.querySelector('.card-header');
                    const collapse = r.querySelector('.collapse');
                    const btn = r.querySelector('button.title');
                    return {
                        class: r.className,
                        h4_aria: h4 ? h4.getAttribute('aria-label') : null,
                        h4_text: h4 ? (h4.textContent||'').trim() : null,
                        header_classes: header ? header.className : null,
                        header_target: header ? header.getAttribute('href') : null,
                        button_aria_expanded: btn ? btn.getAttribute('aria-expanded') : null,
                        collapse_id: collapse ? collapse.id : null,
                        collapse_classes: collapse ? collapse.className : null,
                    };
                });
            }"""
        )
        findings["steps"].append({"step": "refinement_sections", "sections": sections_probe})

        # Look at one refinement DOM to understand expand/collapse markers
        try:
            first_refinement_html = page.locator(".refinement").first.evaluate(
                "el => el.outerHTML"
            )
            findings["steps"].append(
                {"step": "first_refinement_excerpt", "html": first_refinement_html[:1500]}
            )
        except Exception as exc:
            findings["steps"].append({"step": "first_refinement_excerpt", "error": str(exc)})

        # Toggle Curriculum via .refinement-curriculum .card-header click
        try:
            section_sel = ".refinement.refinement-curriculum"
            header_sel = f"{section_sel} .card-header"
            collapse_sel = f"{section_sel} .collapse"
            page.locator(header_sel).first.scroll_into_view_if_needed()
            before = page.evaluate(
                """(sel) => {
                    const h = document.querySelector(sel + ' .card-header');
                    const c = document.querySelector(sel + ' .collapse');
                    return {header: h?.className, collapse: c?.className};
                }""",
                section_sel,
            )
            page.locator(header_sel).first.click()
            page.wait_for_timeout(800)
            after = page.evaluate(
                """(sel) => {
                    const h = document.querySelector(sel + ' .card-header');
                    const c = document.querySelector(sel + ' .collapse');
                    return {header: h?.className, collapse: c?.className};
                }""",
                section_sel,
            )
            findings["steps"].append({"step": "curriculum_toggle", "before": before, "after": after})
        except Exception as exc:
            findings["steps"].append({"step": "curriculum_toggle", "error": str(exc)})

        # Probe Clear All button
        clear_probe = {}
        for sel in [
            'button.reset',
            'a.reset',
            'button:has-text("Clear All")',
            'a:has-text("Clear All")',
            ".secondary-bar a.reset",
            ".secondary-bar button.reset",
        ]:
            clear_probe[sel] = page.locator(sel).count()
        findings["steps"].append({"step": "clear_all_probe", "counts": clear_probe})

        # Detailed tile HTML excerpt
        try:
            first_tile_html = page.evaluate(
                """() => {
                    const t = document.querySelector('.product-tile') || document.querySelector('.product[data-pid]');
                    return t ? t.outerHTML.slice(0, 4000) : null;
                }"""
            )
            findings["steps"].append({"step": "first_tile_html", "html": first_tile_html})
        except Exception as exc:
            findings["steps"].append({"step": "first_tile_html", "error": str(exc)})

        # First product tile + price + add to cart - probe via JS
        tile_probe = page.evaluate(
            """() => {
                const tile = document.querySelector('.product-tile, .product[data-pid], .product');
                if (!tile) return {found:false};
                const out = {found:true, classes: tile.className, id: tile.id};
                // get attributes
                out.attrs = {};
                for (const a of tile.attributes) out.attrs[a.name] = a.value;
                out.priceCandidates = [];
                for (const sel of ['.item-your-price','.price-value','.product-sales-price.our-price .price-value','.sales .price-value','.price','.list-price','.value']) {
                    const found = tile.querySelector(sel);
                    if (found) out.priceCandidates.push({sel, text: (found.textContent||'').trim().slice(0,40)});
                }
                out.buttonCandidates = [];
                for (const sel of ['button.add-to-cart','button[data-satellite-key="add-to-cart-button"]','button.btn-add-to-cart','a.add-to-cart','button[data-action="add-to-cart"]']) {
                    const found = tile.querySelector(sel);
                    if (found) out.buttonCandidates.push({sel, text: (found.textContent||'').trim().slice(0,40), classes: found.className.toString()});
                }
                out.allButtons = Array.from(tile.querySelectorAll('button')).map(b => ({classes: b.className, text: (b.textContent||'').trim().slice(0,40), aria: b.getAttribute('aria-label')||''})).slice(0,8);
                out.nameText = (tile.querySelector('.product-name, .name, .product-tile-name, .pdp-link, .product-link')||{}).textContent || '';
                return out;
            }"""
        )
        findings["steps"].append({"step": "tile_probe", "info": tile_probe})

        # Click add-to-cart on first tile if discovered
        atc_clicked = None
        for sel in [
            ".product-tile button.add-to-cart",
            ".product-tile button.btn-add-to-cart",
            '.product-tile button[data-satellite-key="add-to-cart-button"]',
            ".product[data-pid] button.add-to-cart",
            ".product button.add-to-cart",
        ]:
            try:
                loc = page.locator(sel).first
                if loc.count() == 0:
                    continue
                loc.scroll_into_view_if_needed()
                loc.click(timeout=8000)
                atc_clicked = sel
                break
            except Exception as exc:
                continue
        findings["steps"].append({"step": "add_to_cart_clicked", "selector": atc_clicked})
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        # Cart page
        try:
            page.locator('a[href$="/en/cart"]').first.click()
            page.wait_for_url("**/cart", timeout=15000)
        except Exception:
            page.goto(
                "https://storefront:storefront@education-qa.scholastic.ca/en/cart",
                wait_until="domcontentloaded",
                timeout=60000,
            )
        try:
            page.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            pass
        findings["steps"].append({"step": "cart_loaded", "url": page.url, "title": page.title()})

        cart_probe = page.evaluate(
            """() => {
                const heading = document.querySelector('h1.page-title, .cart h1, h1');
                const rows = Array.from(document.querySelectorAll('[id^="productRow"], [id^="productRow-"], .cart-line-item, .product-info, .product-line-item, .cart .product-line-item, .row.cart-row, .item, [data-pid]'));
                const probe = {
                    headingText: heading ? (heading.textContent||'').trim() : null,
                    headingTag: heading ? heading.tagName : null,
                    headingClasses: heading ? heading.className : null,
                    rowSelectors: {},
                };
                for (const sel of [
                    '[id^="productRow"]', '[id^="productRow-"]',
                    '.cart-line-item', '.product-line-item',
                    '.cart [data-pid]', 'div[data-pid]', '.product[data-pid]',
                    '.product-info', '.line-item-name'
                ]) probe.rowSelectors[sel] = document.querySelectorAll(sel).length;
                if (rows.length > 0) {
                    const r = rows[0];
                    probe.firstRow = {
                        id: r.id,
                        classes: r.className,
                        attrs: Array.from(r.attributes).reduce((acc,a)=>{acc[a.name]=a.value;return acc;},{}),
                        priceCandidates: ['.item-your-price','.price-value','.line-item-total-price-amount','.unit-price','.line-item-total','.price','.your-price','.value'].map(s=>{const f=r.querySelector(s);return f?{sel:s,text:(f.textContent||'').trim()}:null}).filter(Boolean),
                        nameText: ((r.querySelector('.product-name, .line-item-name, .product-line-item-name, .name, .product-link, .item-name'))||{}).textContent || '',
                    };
                }
                return probe;
            }"""
        )
        findings["steps"].append({"step": "cart_probe", "info": cart_probe})

        OUT.write_text(json.dumps(findings, indent=2), encoding="utf-8")
        print(f"Wrote {OUT}")
        print(json.dumps(findings, indent=2)[:6000])

        context.close()
        browser.close()


if __name__ == "__main__":
    sys.exit(main())
