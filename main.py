#!/usr/bin/env python3
"""
Auto-connect Playwright (async) to an already-running Chrome via CDP on 127.0.0.1:9222.

Requirements:
  pip install playwright requests
  playwright install chromium

Make sure Chrome/Chromium is started with:
  chrome --remote-debugging-port=9222
"""
import json
import asyncio
import requests
from playwright.async_api import async_playwright
from backend.services.instagram_scraper.config import ScrapeConfig
from backend.services.instagram_scraper.utils_logger import make_logger

from backend.services.instagram_scraper.follower_scraper import InstagramFollowerScraper
    
STATE_PATH = "./instagram.storage.json"
COOKIES_PATH = "./instagram.cookies.json"


def get_ws_url() -> str:
    """
     fetch the websocketDebuggerUrl  so we can connect to browser.
    """
    resp = requests.get("http://127.0.0.1:9222/json/version", timeout=3)
    resp.raise_for_status()
    return resp.json()["webSocketDebuggerUrl"]


from pathlib import Path

COOKIES_DIR = Path.cwd() / "cookies"

def find_user_cookies(username: str):
    """Find the most recent cookie file for the given username."""
    pattern = f"{username}_*_cookies.json"
    matches = sorted(COOKIES_DIR.glob(pattern))
    if not matches:
        print(f"No cookie files found for username: {username}")
        return None
    latest = max(matches, key=lambda p: p.stat().st_mtime)
    print(f"✅ Found cookie file: {latest}")
    return latest

async def main():

    async with async_playwright() as p:

        # if you want to attach to an existing chrome session we can connect to chrome via cdp, this is for debugging only currently.
        # ws_url = get_ws_url()
        # print(f"[info] Connecting to {ws_url}")
        # browser = await p.chromium.connect_over_cdp(ws_url)


        # # Reuse existing context if available, otherwise create new
        # context = browser.contexts[0] if browser.contexts else await browser.new_context()

        # page = context.pages[0]

        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()


        username = input('type in your instagram username.')

        # find the file with username prefixed file ending with suffix cookies in cookies folder of cwd
        cookie_file = find_user_cookies(username)

        if cookie_file:
            import json
            cookies = json.loads(cookie_file.read_text(encoding="utf-8"))
            print(f"Loaded {len(cookies)} cookies from {cookie_file}")
            await context.add_cookies(cookies)

        page = await context.new_page()


        await page.goto(f'https://instagram.com/{username}')

        await page.wait_for_selector('[href*="followers"]')

        await page.click('[href*="followers"]')

        print(f"[info] Opened {page.url}")
        print(f"[info] Title: {await page.title()}")
        await asyncio.sleep(2)
        logger = make_logger(
            name="ig_followers",
            to_console=True,
            level="DEBUG",
        )

        scraper = InstagramFollowerScraper(
        page,
        config=ScrapeConfig(
        quiet_ms=5_000,
        scroll_delta=1_000,
        cooldown_s=0.1,
        log_to_console=True,      
        log_level="INFO",        
        write_file="followers.json",
            ),
    logger=logger,
            )
        await scraper.run()

        print('wrote followers.json to disk')



        await page.goto(f'https://instagram.com/{username}')

        await asyncio.sleep(2)

        await page.wait_for_selector('[href*="following"]')

        await page.click('[href*="following"]')



        following_scraper = InstagramFollowerScraper(
        page,
        config=ScrapeConfig(
        quiet_ms=5_000,
        scroll_delta=1_000,
        cooldown_s=0.1,
        log_to_console=True,      
        log_level="INFO",        
        write_file="following.json",
            ),
    logger=logger,
            )
        following = await following_scraper.run()

        await asyncio.sleep(3000)

        print('written folllowing.json to disc')


if __name__ == "__main__":
    asyncio.run(main())
