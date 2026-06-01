"""Quick headless probe of the education-qa storefront login affordances."""
from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "https://storefront:storefront@education-qa.scholastic.ca/en/home"


def main() -> None:
    out = Path("reports/login_probe.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    findings: dict = {"steps": []}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1600, "height": 1000},
            http_credentials={"username": "storefront", "password": "storefront"},
            ignore_https_errors=True,
        )
        page = context.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=45000)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        findings["steps"].append({
            "step": "header_counts",
            "a#myaccount": page.locator("a#myaccount").count(),
            "a.signModal": page.locator("a.signModal").count(),
            "iframe_count": page.locator("iframe").count(),
            "iframe_sp": page.locator("iframe[id^='sp_message_iframe_']").count(),
            "any_iframe_ids": [
                page.locator("iframe").nth(i).get_attribute("id")
                for i in range(min(page.locator("iframe").count(), 8))
            ],
            "cookie_btn_main": page.locator("button#onetrust-accept-btn-handler").count(),
        })

        # Try clicking Accept All Cookies in any iframe
        accepted = False
        for i in range(page.locator("iframe").count()):
            try:
                fr = page.frames[i + 1] if i + 1 < len(page.frames) else None
                if fr is None:
                    continue
                btn = fr.locator("button:has-text('Accept All Cookies'), button[title='Accept All Cookies']").first
                if btn.count() and btn.is_visible():
                    btn.click()
                    accepted = True
                    break
            except Exception:
                continue
        findings["steps"].append({"step": "cookies_accepted_in_frame", "ok": accepted})

        # Click sign-in link
        clicked = None
        for sel in ["a#myaccount", "a.signModal[aria-label='Login to your account']", "header a:has-text('Sign In')", "header a:has-text('Educator Sign In')"]:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible():
                try:
                    loc.click()
                    clicked = sel
                    break
                except Exception:
                    continue
        findings["steps"].append({"step": "signin_click", "selector": clicked})
        page.wait_for_timeout(2000)

        findings["steps"].append({
            "step": "form_counts_after_signin",
            "form#dwfrm_login": page.locator("form#dwfrm_login").count(),
            "form#loginForm": page.locator("form#loginForm").count(),
            "any role=dialog": page.locator("[role='dialog']").count(),
            "input[name^='dwfrm_login_username']": page.locator("input[name^='dwfrm_login_username']").count(),
            "input.email-input": page.locator("input.email-input").count(),
            "input[type='password']:visible": page.locator("input[type='password']:visible").count(),
            "input[type='email']:visible": page.locator("input[type='email']:visible").count(),
            "button[name='dwfrm_login_login']": page.locator("button[name='dwfrm_login_login']").count(),
        })

        # Inspect HTML around forms
        try:
            forms = page.locator("form").all()
            form_info = []
            for f in forms:
                try:
                    fid = f.get_attribute("id") or ""
                    fname = f.get_attribute("name") or ""
                    faction = f.get_attribute("action") or ""
                    inputs = f.locator("input").all()
                    input_info = []
                    for inp in inputs[:8]:
                        try:
                            input_info.append({
                                "name": inp.get_attribute("name"),
                                "type": inp.get_attribute("type"),
                                "id": inp.get_attribute("id"),
                                "placeholder": inp.get_attribute("placeholder"),
                            })
                        except Exception:
                            continue
                    form_info.append({"id": fid, "name": fname, "action": faction, "inputs": input_info})
                except Exception:
                    continue
            findings["steps"].append({"step": "all_forms", "forms": form_info[:6]})
        except Exception:
            pass

        out.write_text(json.dumps(findings, indent=2), encoding="utf-8")
        print(json.dumps(findings, indent=2))
        browser.close()


if __name__ == "__main__":
    main()
