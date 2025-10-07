# save_as: login_and_save_ig_cookies.py
import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

# where the users cookie or login session is saved.
BASE_DIR = Path.cwd() / "cookies"

async def wait_for_user_confirmation(prompt: str) -> None:
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, lambda: input(prompt))

def sanitize_username(s: str) -> str:
    # allow letters, numbers, underscore, dot, dash; replace others with underscore
    s = s.strip()
    s = s if s else "user"
    return re.sub(r"[^A-Za-z0-9._-]", "_", s)

async def main():
    BASE_DIR.mkdir(parents=True, exist_ok=True)

    # Prompt for username to tag the files
    username = sanitize_username(input("Instagram username to tag the files (e.g. my_handle): ").strip())
    today = datetime.now().strftime("%Y-%m-%d")

    state_path = BASE_DIR / f"{username}_{today}_state.json"
    cookies_path = BASE_DIR / f"{username}_{today}_cookies.json"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("Opening Instagram…")
        await page.goto("https://www.instagram.com/", wait_until="domcontentloaded")

        print("\n1) Log in to Instagram in the opened window (complete any 2FA).")
        print("2) Once you see your home/feed/profile, come back here.")
        await wait_for_user_confirmation("\nPress ENTER when you're logged in… ")

        # Save storage state (cookies + localStorage)
        await context.storage_state(path=str(state_path))

        # Save raw cookies as well
        cookies = await context.cookies()
        with open(cookies_path, "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)

        print(f"\nSaved storage state → {state_path}")
        print(f"Saved cookies       → {cookies_path}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
