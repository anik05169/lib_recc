"""Capture portfolio screenshots of working Library AI flows."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "screenshots"
BASE = "http://127.0.0.1:5175"
API = "http://127.0.0.1:8000"


def api(method: str, path: str, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(API + path, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else None


def wait_health():
    for _ in range(40):
        try:
            with urllib.request.urlopen(API + "/health", timeout=5) as resp:
                if resp.status == 200:
                    return
        except Exception:
            pass
        time.sleep(0.5)
    raise RuntimeError("API health check failed")


def ensure_creds():
    email = f"shots_ui_{int(time.time())}@example.com"
    password = "TestPass123!"
    try:
        api(
            "POST",
            "/auth/register",
            {"email": email, "password": password, "name": "Shot User"},
        )
    except urllib.error.HTTPError:
        pass
    login = api("POST", "/auth/login", {"email": email, "password": password})
    token = login["access_token"]
    for book_id in (41, 26, 1, 8900, 3187, 212):
        api("POST", f"/user/add-from-catalog?book_id={book_id}", token=token)
    return email, password


def wait_recs_loaded(page, empty_phrase: str, timeout: int = 25000):
    page.wait_for_function(
        """(emptyPhrase) => {
          const box = document.querySelector('.recommendation-box');
          if (!box) return false;
          const t = (box.innerText || '').toLowerCase();
          if (t.includes('loading')) return false;
          if (t.includes(emptyPhrase.toLowerCase())) return false;
          return !!box.querySelector('.recommend-list li');
        }""",
        arg=empty_phrase,
        timeout=timeout,
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    wait_health()
    email, password = ensure_creds()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})

        page.goto(BASE, wait_until="networkidle")
        page.wait_for_selector("#login-email", timeout=20000)
        page.screenshot(path=str(OUT / "01-login.png"))

        page.fill("#login-email", email)
        page.fill("#login-password", password)
        with page.expect_response(lambda r: "/auth/login" in r.url and r.ok, timeout=20000):
            page.click('button[type="submit"]')
        page.wait_for_selector(".nav-tabs, .book-list", timeout=20000)
        page.wait_for_timeout(1000)

        catalog_tab = page.get_by_role("button", name="Explore Catalog")
        if catalog_tab.count():
            catalog_tab.click()
            page.wait_for_timeout(600)

        page.screenshot(path=str(OUT / "02-catalog.png"))

        search = page.locator('input[placeholder*="Search"], input[type="search"]').first
        search.fill("Lightning Thief")
        page.wait_for_timeout(1200)
        page.get_by_text("The Lightning Thief (", exact=False).first.wait_for(timeout=20000)

        with page.expect_response(lambda r: "/recommend/" in r.url and r.ok, timeout=20000):
            page.get_by_role("button", name="Similar books").first.click()
        wait_recs_loaded(page, "No related books found")
        page.locator(".recommendation-box").first.scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        page.screenshot(path=str(OUT / "03-catalog-recommendations.png"))

        page.get_by_role("button", name="My Collection").click()
        page.wait_for_timeout(900)

        # AI panel (top of collection)
        ai_area = page.locator("text=/AI suggestions|Get recommendations/i").first
        if ai_area.count():
            ai_area.scroll_into_view_if_needed()
            page.wait_for_timeout(300)
            page.screenshot(path=str(OUT / "06-ai-suggest.png"))

        # Collection grid
        page.locator(".book-list .book-card").first.wait_for(timeout=15000)
        page.locator(".book-list").first.scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        page.screenshot(path=str(OUT / "04-collection.png"))

        # Dual recommend on Lightning Thief when present
        lightning_card = page.locator(".book-card").filter(
            has_text="The Lightning Thief (Percy Jackson"
        ).first
        target = lightning_card if lightning_card.count() else page.locator(".book-card").first
        find_btn = target.get_by_role("button", name="Find similar")
        with page.expect_response(
            lambda r: "/user/recommend/" in r.url and r.ok, timeout=30000
        ):
            find_btn.click()
        wait_recs_loaded(page, "No similar books found in the catalog", timeout=30000)
        target.locator(".recommendation-box").scroll_into_view_if_needed()
        page.wait_for_timeout(500)
        # Crop to the expanded card so both recommendation sections are visible
        target.screenshot(path=str(OUT / "05-library-dual-recommendations.png"))

        browser.close()

    # Remove debug artifacts
    for debug in OUT.glob("_debug_*.png"):
        debug.unlink()

    print("Screenshots written to", OUT)
    for f in sorted(OUT.iterdir()):
        if f.suffix == ".png":
            print(f"  {f.name} ({f.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
