import json
from .follower_scraper import InstagramFollowerScraper
from typing import Optional, List, Dict
from .config import ScrapeConfig, Selectors
from .dom_activity_observer import DomActivityObserver
from .mouse_event_scroller import WheelEventScroller
from .loading_detector import LoadingDetector

# inherits from the basic instagram scraper and overrides the scrape method to extract and update follower list in real time
class LiveInstagramFollowerScraper(InstagramFollowerScraper):

    def __init__(self, page, config: Optional[ScrapeConfig] = None, selectors: Optional[Selectors] = None, logger=None):
        self.follower_list = []
        # keep track of the followers retrieved from the dom in a set, that way we can detect duplicates in constant time
        self.follower_set = set()
        super().__init__(page, config, selectors , logger)
    

    def reset_follower_scrape(self):
        self.follower_list = []
        self.follower_set = set()

    
    def add_unique_follower(self, f):
        key = json.dumps(f, sort_keys=True)
        if key not in self.follower_set:
            self.follower_set.add(key)
            self.follower_list.append(f)
            return True
        return False

    def write_followers_to_disk(self, new_followers=None):
        if not self.config.write_file:
            self.log.warning("No write_file path configured; skipping write.")
            return
        try:
            with open(self.config.write_file, "w", encoding="utf-8") as f:
                json.dump(self.follower_list, f, indent=4, ensure_ascii=False)
            if new_followers and len(new_followers) > 0:
                self.log.info(f"Added {len(new_followers)} new followers to the follower list.")
        except Exception as e:
            self.log.error(f"Failed to write followers to disk: {e}")
            print(f"Write failed: {e}")

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
                    # if it was loading and loading animation does not exist, we can scroll again
                    if await self.loading.poll_once(self.page) is not True:
                        break
                    await self.loading.wait_small()
            
            current_followers_list = await self._parse_followers()

            new_followers = []
            # after we scroll down, the dom will have followers which were added previously, 
            # so add only unique followers that aren't already captured in memory
            for follower in current_followers_list:
                is_follower_new = self.add_unique_follower(follower)
                if is_follower_new:
                    new_followers.append(follower)
            

            self.write_followers_to_disk(new_followers)
            
            if await self.dom_observer.is_stable(self.page):
                self.log.info(f"DOM stabilized after {i+1} scrolls")
                break

            await self.loading.wait_small()
        

        # after dom stablization parse the follower list once again
        current_followers_list = await self._parse_followers()

        new_followers = []

        for follower in current_followers_list:
            is_it_unique = self.add_unique_follower(follower)
            if is_it_unique:
                new_followers.append(follower)
        

        self.write_followers_to_disk(new_followers)


        return self.follower_list

        


        self.log.info(f"Scraped a total of {len(self.follower_list)} followers")

