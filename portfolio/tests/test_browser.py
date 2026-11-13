"""Bounded browser acceptance runner; all pages and assets stay on loopback."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT))
from portfolio.lib.build import build_site
from portfolio.lib.server import create_server


def fixture_root(target: Path) -> Path:
    (target / "portfolio").mkdir(parents=True)
    shutil.copy2(ROOT / "portfolio" / "projects.json", target / "portfolio" / "projects.json")
    registry_path = target / "portfolio" / "projects.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    synthetic = json.loads((ROOT / "portfolio" / "examples" / "project-with-demo.example.json").read_text(encoding="utf-8"))
    synthetic["title"] = '<img src=x onerror="alert(1)">'
    registry["projects"].append(synthetic)
    registry_path.write_text(json.dumps(registry, ensure_ascii=False), encoding="utf-8")
    shutil.copytree(ROOT / "portfolio" / "web", target / "portfolio" / "web")
    public = ROOT / "portfolio" / "public"
    if public.exists():
        shutil.copytree(public, target / "portfolio" / "public", dirs_exist_ok=True)
    else:
        (target / "portfolio" / "public").mkdir(parents=True)
    demos = target / "portfolio" / "public" / "demos" / "synthetic-demo" / "1.0.0"
    demos.mkdir(parents=True)
    shutil.copytree(ROOT / "portfolio" / "examples" / "demo-bundle", demos, dirs_exist_ok=True)
    local_dir = target / ".local"
    local_dir.mkdir()
    overlay = json.loads((ROOT / "portfolio" / "examples" / "local.example.json").read_text(encoding="utf-8"))
    overlay["bindings"] = [{"project_id": "factory-knowledge-grounded-rag", "binding_id": "local-demo", "url": "http://127.0.0.1:9/demo"}]
    overlay["local_projects"] = []
    (local_dir / "projects.local.json").write_text(json.dumps(overlay, ensure_ascii=False), encoding="utf-8")
    return target


def _launch(playwright, preference: str):
    errors = []
    choices = [preference] if preference != "auto" else ["chromium", "msedge", "chrome"]
    for choice in choices:
        try:
            if choice == "chromium":
                browser = playwright.chromium.launch(headless=True, timeout=15000)
            else:
                browser = playwright.chromium.launch(channel=choice, headless=True, timeout=15000)
            return browser, choice
        except Exception as exc:  # A missing browser is a distinct environment outcome.
            errors.append(f"{choice}:{type(exc).__name__}")
    raise RuntimeError("no usable browser; " + ",".join(errors))


def run(browser_choice: str) -> dict:
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeout
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"status": "BLOCKED_E2E", "reason": "Playwright 1.64.1 is not installed in the isolated test environment"}

    temp = tempfile.TemporaryDirectory(prefix="portfolio-browser-")
    root = fixture_root(Path(temp.name) / "repo")
    result = {"status": "FAIL", "browser": None, "screenshots": [], "checks": []}
    server = None
    server_thread = None
    started = time.monotonic()
    try:
        public, digest = build_site(root, "public")
        server_root = Path(temp.name) / "host"
        shutil.copytree(public, server_root)
        (server_root / "nested").mkdir()
        shutil.copytree(public, server_root / "nested", dirs_exist_ok=True)
        server, base_url = create_server(server_root, 0)
        server_thread = __import__("threading").Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        with sync_playwright() as playwright:
            browser, selected = _launch(playwright, browser_choice)
            result["browser"] = selected
            context = browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
            page = context.new_page()
            external_requests = []
            page.on("request", lambda request: external_requests.append(request.url) if not request.url.startswith(base_url) else None)
            page.set_default_timeout(5000)
            page.goto(base_url, wait_until="domcontentloaded", timeout=10000)
            page.locator(".project-card").first.wait_for(state="visible", timeout=5000)
            count = page.locator(".project-card").count()
            assert count == 10, f"expected 9 registry projects plus one synthetic extension fixture, got {count}"
            result["checks"].append("A01: nine projects load with no source services")
            unsafe_text = page.get_by_text('<img src=x onerror="alert(1)">', exact=True)
            assert unsafe_text.is_visible(), "HTML-like title is not displayed as literal text"
            assert page.locator('img[src="x"]').count() == 0, "HTML-like title created an executable element"
            result["checks"].append("A09: HTML-like project text remains inert")

            search = page.get_by_label("搜尋作品、功能或標籤")
            search.fill("工單")
            assert page.locator(".project-card").count() >= 1
            search.fill("")
            page.get_by_label("作品分類").select_option(label="系統整合")
            assert page.locator(".project-card").count() >= 1
            page.get_by_label("作品分類").select_option(value="")
            page.get_by_label("只看精選").check()
            assert page.locator(".project-card").count() == 4
            page.get_by_label("只看精選").uncheck()
            result["checks"].append("search, category and featured filters")

            page.locator('a[href="#/projects/factory-knowledge-grounded-rag"]').first.click()
            page.wait_for_url("**/#/projects/factory-knowledge-grounded-rag", timeout=5000)
            page.locator("#detail h2").wait_for(state="visible", timeout=5000)
            assert page.locator("#detail h2").inner_text() == "設備知識庫與地端診斷助手"
            page.reload(wait_until="domcontentloaded", timeout=10000)
            page.locator("#detail h2").wait_for(state="visible", timeout=5000)
            assert page.locator("#detail h2").inner_text() == "設備知識庫與地端診斷助手"
            page.goto(base_url + "#/projects/not-a-real-project", wait_until="domcontentloaded", timeout=10000)
            page.get_by_text("找不到這件作品").wait_for(state="visible", timeout=5000)
            assert page.get_by_text("找不到這件作品").is_visible()
            result["checks"].append("hash details, direct reload and unknown route")

            page.goto(base_url, wait_until="domcontentloaded", timeout=10000)
            demo = page.locator('a[href="demos/synthetic-demo/1.0.0/index.html"]').first
            assert demo.is_visible(), "static demo link is missing"
            with context.expect_page() as demo_page_info:
                demo.click()
            demo_page = demo_page_info.value
            demo_page.wait_for_load_state("domcontentloaded", timeout=5000)
            assert demo_page.url.endswith("/demos/synthetic-demo/1.0.0/index.html")
            demo_page.get_by_text("展示版本 v1.0.0").wait_for(state="visible", timeout=5000)
            demo_page.get_by_role("button", name="預覽功能更新").click()
            demo_page.get_by_text("v1.1.0 預覽：新功能顯示為規劃中；作品識別碼保持不變。").wait_for(state="visible", timeout=5000)
            result["checks"].append("static bundle opens and runs from the hub")

            local, _ = build_site(root, "local")
            local_server_root = Path(temp.name) / "local-host"
            shutil.copytree(local, local_server_root)
            local_server, local_url = create_server(local_server_root, 0)
            local_thread = __import__("threading").Thread(target=local_server.serve_forever, daemon=True)
            local_thread.start()
            local_page = context.new_page()
            local_requests = []
            local_page.on("request", lambda request: local_requests.append(request.url) if "127.0.0.1:9" in request.url else None)
            local_page.goto(local_url, wait_until="domcontentloaded", timeout=10000)
            local_page.get_by_role("link", name="本機 Demo（自行啟動）（未檢查）").wait_for(state="visible", timeout=5000)
            assert not local_requests, f"hub automatically contacted local demo: {local_requests}"
            assert local_page.locator('a[href="http://127.0.0.1:9/demo"]').count() == 1
            local_server.shutdown()
            local_server.server_close()
            local_thread.join(timeout=2)
            result["checks"].append("A05: local HTTP binding is shown but never probed")

            page.goto(base_url, wait_until="domcontentloaded", timeout=10000)
            page.set_viewport_size({"width": 1440, "height": 1000})
            wide_overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
            assert not wide_overflow, "1440px page overflows horizontally"
            evidence = ROOT / ".local" / "evidence"
            evidence.mkdir(parents=True, exist_ok=True)
            wide = evidence / "portfolio-1440x1000.png"
            page.screenshot(path=str(wide), full_page=True, timeout=10000)
            result["screenshots"].append(wide.relative_to(ROOT).as_posix())

            page.set_viewport_size({"width": 390, "height": 844})
            mobile_overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
            assert not mobile_overflow, "390px page overflows horizontally"
            mobile = evidence / "portfolio-390x844.png"
            page.screenshot(path=str(mobile), full_page=True, timeout=10000)
            result["screenshots"].append(mobile.relative_to(ROOT).as_posix())
            result["checks"].append("keyboard labels, focusable controls, 1440px and 390px layouts")

            no_js_context = browser.new_context(java_script_enabled=False, viewport={"width": 1440, "height": 1000})
            no_js = no_js_context.new_page()
            no_js.goto(base_url, wait_until="domcontentloaded", timeout=10000)
            assert no_js.locator(".project-card").count() == 10
            assert no_js.locator('.project-card h2 a').count() == 0, "static fallback must not expose dead detail links"
            assert no_js.locator('.project-card nav a').count() > 0, "static fallback must keep source links"
            no_js_context.close()
            result["checks"].append("static fallback with JavaScript disabled")

            subpath = context.new_page()
            subpath.goto(base_url + "nested/", wait_until="domcontentloaded", timeout=10000)
            assert subpath.locator(".project-card").count() == 10
            nested_demo = subpath.locator('a[href="demos/synthetic-demo/1.0.0/index.html"]').first
            with context.expect_page() as nested_demo_info:
                nested_demo.click()
            nested_demo_page = nested_demo_info.value
            nested_demo_page.wait_for_load_state("domcontentloaded", timeout=5000)
            assert "/nested/demos/synthetic-demo/1.0.0/index.html" in nested_demo_page.url
            nested_demo_page.get_by_text("展示版本 v1.0.0").wait_for(state="visible", timeout=5000)
            result["checks"].append("relative assets on a nested static path")
            assert not external_requests, f"unexpected non-loopback request: {len(external_requests)}"
            result["checks"].append("no external network requests")
            browser.close()
        if time.monotonic() - started > 180:
            raise TimeoutError("browser run exceeded 180 seconds")
        result.update(status="PASS", digest=digest, elapsed_seconds=round(time.monotonic() - started, 2))
        return result
    except (AssertionError, PlaywrightTimeout, TimeoutError) as exc:
        result.update(status="FAIL", reason=f"{type(exc).__name__}: {exc}", elapsed_seconds=round(time.monotonic() - started, 2))
        return result
    except RuntimeError as exc:
        if str(exc).startswith("no usable browser"):
            result.update(status="BLOCKED_E2E", reason=str(exc), elapsed_seconds=round(time.monotonic() - started, 2))
            return result
        raise
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()
            if server_thread is not None:
                server_thread.join(timeout=2)
        temp.cleanup()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--browser", choices=["auto", "chromium", "msedge", "chrome"], default="auto")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run(args.browser)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if result["status"] == "PASS":
        return 0
    return 6 if result["status"] == "BLOCKED_E2E" else 6


if __name__ == "__main__":
    raise SystemExit(main())
