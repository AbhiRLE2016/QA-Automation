"""Quick probe: snapshot DOM state right after page load."""
from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
URL = "https://storefront:storefront@education-qa.scholastic.ca/en/home"
OUT = ROOT / "mcp-selectors" / "discovery_probe.json"


def main():
    findings = {}
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
        # Wait additional 5s for header rehydration
        page.wait_for_timeout(5000)
        findings["url"] = page.url
        findings["title"] = page.title()
        findings["counts"] = {
            "a#myaccount": page.locator("a#myaccount").count(),
            "a.signModal": page.locator("a.signModal").count(),
            "form#dwfrm_login": page.locator("form#dwfrm_login").count(),
            "form#loginForm": page.locator("form#loginForm").count(),
            "input.search-field": page.locator("input.search-field").count(),
            "header": page.locator("header").count(),
            "nav.main-menu": page.locator("nav.main-menu").count(),
            "all forms": page.locator("form").count(),
            "all iframes": page.locator("iframe").count(),
            ".product-tile": page.locator(".product-tile").count(),
        }
        # Capture top of body HTML
        body = page.evaluate("() => document.body.outerHTML.slice(0, 4000)")
        findings["body_top"] = body
        # Capture all visible link texts in header area
        try:
            hdr = page.evaluate(
                """() => {
                    const out = [];
                    const els = document.querySelectorAll('a, button');
                    for (const el of els) {
                        const r = el.getBoundingClientRect();
                        if (r.width > 0 && r.height > 0 && r.top < 200) {
                            out.push({
                                tag: el.tagName,
                                id: el.id,
                                cls: el.className.toString().slice(0, 80),
                                text: (el.textContent || '').trim().slice(0, 40),
                                href: el.getAttribute('href') || '',
                                aria: el.getAttribute('aria-label') || '',
                            });
                        }
                    }
                    return out.slice(0, 60);
                }"""
            )
            findings["header_actions"] = hdr
        except Exception as exc:
            findings["header_actions"] = {"error": str(exc)}

        OUT.write_text(json.dumps(findings, indent=2), encoding="utf-8")
        print(f"Wrote {OUT}")
        print(json.dumps(findings, indent=2)[:8000])

        context.close()
        browser.close()


if __name__ == "__main__":
    main()
