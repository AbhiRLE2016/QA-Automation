"""Phase-3 probe: dismiss CMP, fire various click techniques, watch AJAX."""
from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "https://storefront:storefront@bookclubs-qa.scholastic.ca/en/home"


def dismiss_cmp(page) -> bool:
    candidates = [
        "button:has-text('Accept All Cookies')",
        "button:has-text('Accept All')",
        "button:has-text('Accept')",
        "button[aria-label*='Accept' i]",
    ]
    page.wait_for_timeout(2500)
    for frame in list(page.frames):
        if frame is page.main_frame:
            continue
        for sel in candidates:
            try:
                btn = frame.locator(sel).first
                if btn.count() and btn.is_visible():
                    try:
                        btn.click(timeout=3000)
                    except Exception:
                        btn.click(timeout=3000, force=True)
                    page.wait_for_timeout(1500)
                    return True
            except Exception:
                continue
    return False


def main() -> None:
    out = Path("reports/probe_bookclubs3")
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1600, "height": 1000},
            http_credentials={"username": "storefront", "password": "storefront"},
            ignore_https_errors=True,
        )
        page = context.new_page()

        net: list[dict] = []
        page.on("request", lambda r: net.append({"req": f"{r.method} {r.url}"}))
        page.on("response", lambda r: net.append({"res": f"{r.status} {r.url}"}))

        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        cmp_ok = dismiss_cmp(page)
        print("CMP dismissed:", cmp_ok)

        # Inspect candidate
        link = page.locator("a.signInLink-wrapper").first
        attrs = link.evaluate(
            "el => ({outer: el.outerHTML, parent: el.parentElement.outerHTML.substring(0,300), bounding: JSON.stringify(el.getBoundingClientRect())})"
        )
        Path(out / "01_link_attrs.json").write_text(json.dumps(attrs, indent=2), encoding="utf-8")

        # Try several click techniques in sequence and check modal visibility after each
        techniques = [
            ("plain", lambda: link.click(timeout=4000)),
            ("force", lambda: link.click(timeout=4000, force=True)),
            ("dispatch", lambda: link.dispatch_event("click")),
            ("js_click", lambda: link.evaluate("el => el.click()")),
            ("jquery_click", lambda: page.evaluate("() => { if (window.jQuery) { jQuery('a.signInLink-wrapper').trigger('click'); } }")),
        ]

        modal_states = []
        for name, fn in techniques:
            try:
                fn()
            except Exception as e:
                modal_states.append({"tech": name, "err": str(e)})
                continue
            page.wait_for_timeout(2500)
            try:
                page.wait_for_load_state("networkidle", timeout=4000)
            except Exception:
                pass
            visible = False
            ajax_filled = False
            try:
                cls = page.locator("#signInModal").first.get_attribute("class") or ""
                style = page.locator("#signInModal").first.get_attribute("style") or ""
                ajax_html_len = len(page.locator("#signInModal .dialogAjaxData").first.inner_html(timeout=1000) or "")
                visible = ("show" in cls) or ("display: block" in style)
                ajax_filled = ajax_html_len > 100
            except Exception:
                pass
            modal_states.append(
                {
                    "tech": name,
                    "modal_class": cls,
                    "modal_style": style,
                    "ajax_html_len": ajax_html_len if "ajax_html_len" in locals() else None,
                    "visible": visible,
                    "ajax_filled": ajax_filled,
                }
            )
            if visible and ajax_filled:
                break

        Path(out / "02_modal_states.json").write_text(json.dumps(modal_states, indent=2), encoding="utf-8")

        # Final state
        try:
            modal_html = page.locator("#signInModal").inner_html(timeout=2000)
            Path(out / "03_signInModal.html").write_text(modal_html, encoding="utf-8")
        except Exception as e:
            Path(out / "03_signInModal.html").write_text(f"err: {e}", encoding="utf-8")

        # Network filtered to suspect endpoints
        rel = [n for n in net if "Account" in n.get("req", n.get("res", ""))
               or "login" in n.get("req", n.get("res", "")).lower()
               or "signin" in n.get("req", n.get("res", "")).lower()]
        Path(out / "04_login_network.txt").write_text(
            "\n".join(json.dumps(x) for x in rel), encoding="utf-8"
        )

        page.screenshot(path=str(out / "05_final.png"), full_page=True)
        browser.close()


if __name__ == "__main__":
    main()
