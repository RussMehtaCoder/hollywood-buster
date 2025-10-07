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

# this invokes the scroll event by sending a negative delta value to the mouse scroll event in js and then 
async def simulate_element_scroll(page, class_name: str, delta_y: int = 100):
    await page.evaluate("""
        ([className, deltaY]) => {
            function simulateElementScroll(className, deltaY = 100) {
                        
                const element = document.querySelector('.x6nl9eh');
                //const element = document.querySelectorAll('.x78zum5.xdt5ytf.x1iyjqo2.xs83m0k.x1xzczws.x6ikm8r.x1odjw0f.x1n2onr6.xh8yej3.x16o0dkt')[1];
                if (!element) {
                    console.error('Element not found:', className);
                    return;
                }

                const event = new WheelEvent('wheel', {
                    deltaY: deltaY,
                    bubbles: true,
                    cancelable: true,
                    view: window
                });

                element.dispatchEvent(event);
                element.scrollBy({ top: deltaY, behavior: 'smooth' });

                console.log(`Scrolled element '${className}' by deltaY: ${deltaY}`);
            }

            simulateElementScroll(className, deltaY);
        }
    """, [class_name, delta_y])
    
    print('scrolled up with delta of -2000')
    

# this checks if the loading state is shown on the page, if it is we do not want to scroll as it is useless to scroll while its loading
async def check_loading_state(page):
    count = 0
    while True:
        try:

            row = await page.query_selector('.x9q68il')

            if row:
                loading_state = await row.query_selector('[data-visualcompletion="loading-state"]')
                # if we notice a loading animation, then we want to spinlock until the loading element exits
                if loading_state:
                    print("Loading state exists.")
                    count += 1
                else:
                    print("Loading state does NOT exist.")
                    # print('we can scroll again')
                    await asyncio.sleep(.1)
                    if count == 0:
                        return False
                    else:
                        return True
                    # return False
                    # break
            else:
                print("Row does not exist.")
                return True
        except Exception as e:
            print(f"Error: {e}")
            return False
        await asyncio.sleep(.1)  # Wait 1 second before polling again

def get_ws_url() -> str:
    """
     fetch the websocketDebuggerUrl  so we can connect to browser.
    """
    resp = requests.get("http://127.0.0.1:9222/json/version", timeout=3)
    resp.raise_for_status()
    return resp.json()["webSocketDebuggerUrl"]

async def inject_dom_observer(page, selector, quiet_ms=10000):
    await page.evaluate(
        """({selector, quietMs}) => {
            window.domObserverFinished = false;

            const target = document.querySelector(selector);
            if (!target) {
                console.log("Target not found!");
                window.domObserverFinished = true;
                return;
            }

            let timeout;
            const observer = new MutationObserver(() => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    observer.disconnect();
                    console.log("No changes for " + quietMs + "ms — stopped watching.");
                    window.domObserverFinished = true;
                }, quietMs);
            });

            observer.observe(target, {
                childList: true,
                subtree: true,
                attributes: true,
                characterData: true
            });

            // fallback
            timeout = setTimeout(() => {
                observer.disconnect();
                console.log("No changes detected in first " + quietMs + "ms");
                window.domObserverFinished = true;
            }, quietMs);

            console.log("👀 Global observer watching", selector);
        }""",
        {"selector": selector, "quietMs": quiet_ms}
    )


async def is_dom_stable(page):
    return await page.evaluate("() => window.domObserverFinished === true")

async def main():
    ws_url = get_ws_url()
    print(f"[info] Connecting to {ws_url}")

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(ws_url)

        username = input('type in your instagram username.')

        # Reuse existing context if available, otherwise create new
        context = browser.contexts[0] if browser.contexts else await browser.new_context()

        page = context.pages[0]

        await page.goto(f'https://instagram.com/{username}')

        await page.wait_for_selector('[href*="followers"]')

        await page.click('[href*="followers"]')

        print(f"[info] Opened {page.url}")
        print(f"[info] Title: {await page.title()}")


        await page.goto(f'https://instagram.com/{username}')

        await page.wait_for_selector('[href*="following"]')

        await page.click('[href*="following"]')

        await simulate_element_scroll(page, 'test', 1000)


        search_input = await page.query_selector('[aria-label="Search input"]')
        await search_input.focus()

        print("focused on input")

        await inject_dom_observer(page, '[aria-label="Search input"]', quiet_ms=10000)

        for i in range(10000000):
            await simulate_element_scroll(page, 'test', 1000)
            did_animation_come = await check_loading_state(page)

            if await is_dom_stable(page):
                print(f"✅ DOM stabilized after {i+1} scrolls")
                break

        data = await page.evaluate("""
        () => {
            return Array.from(
                document.querySelectorAll('[class="x1qnrgzn x1cek8b2 xb10e19 x19rwo8q x1lliihq x193iq5w xh8yej3"]')
            ).map(element => {
                const linkEl = element.querySelector('a[role="link"]');
                const imgEl = linkEl ? linkEl.querySelector('img') : null;
                const nameEl = element.querySelector('[class="x1lliihq x1plvlek xryxfnj x1n2onr6 xyejjpt x15dsfln x193iq5w xeuugli x1fj9vlw x13faqbe x1vvkbs x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x1i0vuye xvs91rp xo1l8bm x1roi4f4 x10wh9bi xpm28yp x8viiok x1o7cslx"]');

                return {
                    username: linkEl ? linkEl.getAttribute('href').slice(1,-1) : null,
                    name: nameEl ? nameEl.textContent.trim() : null,
                    profilePic: imgEl ? imgEl.src : null
                };
            });
        }
    """)
        
    # Print to console for debugging
    print("The follower list is:", data)

    # Write to a prettified JSON file
    with open("followers.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

            # gets all the instagram usernames

        
            # Array.from(document.querySelectorAll('[class="x1qnrgzn x1cek8b2 xb10e19 x19rwo8q x1lliihq x193iq5w xh8yej3"]')).map(element => element.querySelector('a[role="link"]').href)
            # .querySelector("[role='link']").querySelector('img')



    await asyncio.sleep(.1)

if __name__ == "__main__":
    asyncio.run(main())
