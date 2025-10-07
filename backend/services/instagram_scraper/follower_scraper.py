import json
from typing import Optional, List, Dict
from .config import ScrapeConfig, Selectors
from .dom_activity_observer import DomActivityObserver
from .mouse_event_scroller import WheelEventScroller
from .loading_detector import LoadingDetector

class InstagramFollowerScraper:
    """
    Scroll -> (optionally wait while loading graphic is visible) -> check DOM stability.
    Stop ONLY when DOM has been quiet for quiet_ms. Then parse the follower list.
    """
    def __init__(self, page, config: Optional[ScrapeConfig] = None, selectors: Optional[Selectors] = None, logger=None):
        self.page = page
        self.config = config or ScrapeConfig()
        self.selectors = selectors or Selectors()

        self.log = logger 

        self.scroller = WheelEventScroller(logger=self.log)
        self.loading = LoadingDetector(self.selectors, self.config.cooldown_s, logger=self.log)
        self.dom_observer = DomActivityObserver(self.config.quiet_ms, logger=self.log)

    async def run(self) -> List[Dict]:
        self.log.info("Starting follower scrape")
        # Attach observer to the search-area anchor. this is used to determine when lazy loading is complete
        await self._focus_anchor_if_present()
        await self.dom_observer.start(self.page, self.selectors.search_area_anchor_css)

        for i in range(self.config.max_scrolls):
            # attempt a scroll
            await self.scroller.scroll(self.page, self.selectors, self.config.scroll_delta)

            # throttle scrolling while loading graphic is visible (NOT a stop condition)
            loading = await self.loading.poll_once(self.page)
            # if we detect loading spinlock until loading is complete then scroll again
            if loading is True:
                for _ in range(50):  # ~5s if cooldown_s=0.1
                    if await self.dom_observer.is_stable(self.page):
                        break
                    # if it was loading and it no longer loaded, we can scroll again
                    if await self.loading.poll_once(self.page) is not True:
                        break
                    await self.loading.wait_small()

            if await self.dom_observer.is_stable(self.page):
                self.log.info(f"DOM stabilized after {i+1} scrolls")
                break

            await self.loading.wait_small()
        
        # fetches all the followers via JS manipulation
        data = await self._parse_followers()
        self.log.info(f"Parsed {len(data)} followers")


        if self.config.write_file:
            try:
                with open(self.config.write_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                    self.log.info(f"Wrote {len(data)} records to {self.config.write_file}")
            except Exception as e:
                self.log.error(f"Write failed: {e}")
                print(f" write failed: {e}")
        return data

    async def _focus_anchor_if_present(self):
        el = await self.page.query_selector(self.selectors.search_area_anchor_css)
        if el:
            try:
                await el.focus()
                self.log.debug("Focused search-area anchor")
            except Exception as e:
                self.log.debug(f"Focus failed (non-fatal): {e}")
                pass
    


    async def _parse_followers(self) -> List[Dict]:
        """Inline parser for follower rows."""
        sel = self.selectors
        # this will go through each row of followers and grab username, pic, name, and whether they are verified
        return await self.page.evaluate(
    """
    ({ itemSel, linkSel, nameSel, verifySel }) => {
        // Grab all elements in DOM order
        const allEls = Array.from(document.querySelectorAll('*'));

        // Find the index of the first <h4> that contains "Suggested for you"
        const stopIndex = allEls.findIndex(
            el => el.tagName.toLowerCase() === 'h4' && el.textContent.includes('Suggested for you')
        );

        // If not found, take everything
        const limit = stopIndex !== -1 ? stopIndex : allEls.length;

        // Take only itemSel elements before that point as we do not want suggested followers
        const beforeSuggested = allEls.slice(0, limit).filter(el => el.matches(itemSel));

        return beforeSuggested.map(el => {
            const a = el.querySelector(linkSel);
            const nameEl = el.querySelector(nameSel);
            const isVerified = !!el.querySelector(verifySel);
            const img =
                a?.querySelector?.('img') ??
                // if the instagram user is verified their profile pic is in a span tag
                el.querySelector('span[role="link"] img') ??
                null;

            let username = null;
            if (a) {
                const href = a.getAttribute('href') || "";
                // trim the forward slash at the begging and end
                username = href.replace(/^\\/+|\\/+$/g, '');
            }

            return {
                username,
                name: nameEl ? nameEl.textContent.trim() : null,
                profilePic: img ? img.src : null,
                verified: isVerified
            };
        });
    }
    """,
    {
        "itemSel": sel.follower_item_css,
        "linkSel": sel.follower_link_css,
        "nameSel": sel.follower_name_css,
        "verifySel": sel.verified_bage_css,
    },
)


