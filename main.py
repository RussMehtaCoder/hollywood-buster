#!/usr/bin/env python3
"""
Auto-connect Playwright (async) to an already-running Chrome via CDP on 127.0.0.1:9222.

Requirements:
  pip install playwright requests
  playwright install chromium

Make sure Chrome/Chromium is started with:
.\\chrome.exe --remote-debugging-port=9222 --user-data-dir=%CD%\tmp-profile
"""
import json
import asyncio
import requests
from playwright.async_api import async_playwright
from backend.services.instagram_scraper.config import ScrapeConfig
from backend.services.instagram_scraper.utils_logger import make_logger

from backend.services.instagram_scraper.follower_scraper import InstagramFollowerScraper
from backend.services.instagram_scraper.follower_scraper_live import LiveInstagramFollowerScraper
from backend.services.instagram_scraper.follower_analyzer import FollowerAnalyzer

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
    print(f"Found cookie file: {latest}")
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

        username = input('type in your instagram username.')

        mode = input('live scrape mode? y/n')

        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()


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
        follower_logger = make_logger(
            name="follower_scraper",
            to_console=True,
            level="INFO",
        )

        # Define shared config once
        config = ScrapeConfig(
            quiet_ms=5_000,
            scroll_delta=1_000,
            cooldown_s=0.1,
            log_to_console=True,
            log_level="INFO",
            write_file="followers.json",
        )

        # Choose scraper class based on mode
        ScraperClass = LiveInstagramFollowerScraper if mode == "y" else InstagramFollowerScraper

        # Instantiate scraper
        scraper = ScraperClass(page, config=config, logger=follower_logger)

        
        followers = await scraper.run()

        print('wrote followers.json to disk')



        await page.goto(f'https://instagram.com/{username}')

        await asyncio.sleep(2)

        await page.wait_for_selector('[href*="following"]')

        await page.click('[href*="following"]')

        following_logger = make_logger(
            name="follower_scraper",
            to_console=True,
            level="INFO",
        )

        ScraperClass = LiveInstagramFollowerScraper if mode.lower() == "y" else InstagramFollowerScraper

        # Shared configuration
        config = ScrapeConfig(
            quiet_ms=5_000,
            scroll_delta=1_000,
            cooldown_s=0.1,
            log_to_console=True,
            log_level="INFO",
            write_file="following.json",
        )

        # Instantiate and run scraper
        following_scraper = ScraperClass(
            page,
            config=config,
            logger=following_logger,
        )

        following = await following_scraper.run()


        follower_calculator = FollowerAnalyzer(followers, following, './')


        they_dont_follow_back = follower_calculator.compute_they_dont_follow_back()
        you_dont_follow_back = follower_calculator.compute_you_dont_follow_back()

        follower_calculator._save_json('they_dont_follow_back.json' , they_dont_follow_back)
        follower_calculator._save_json('you_dont_follow_back.json' ,you_dont_follow_back)
    
        print('written folllowing.json to disc')


if __name__ == "__main__":
    asyncio.run(main())
