from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class ScrapeConfig:
    quiet_ms: int = 4_000
    max_scrolls: int = 25_000
    scroll_delta: int = 1_000
    cooldown_s: float = 0.1
    write_file: Optional[str] = "followers.json"
    log_to_console: bool = False          
    log_level: str = "INFO"               

@dataclass(frozen=True)
class Selectors:
    # the scrolling container within the follower list which we can use to load more folloers
    scroll_container_css: str = ".x6nl9eh"

    # class for instagram follower row containing all details about the follower
    # 
    #  
    follower_row_css: str = ".x9q68il"


    # the loading graphic that displays when scrolling down followers 
    # (if its loading, we do not want to scroll until its done loading)                 
    loading_graphic_element: str = '[data-visualcompletion="loading-state"]'



    # logic - we attach a mutation observer to the "search input". 
    # how instagrams dom works is, when we scroll down the follower list, and it loads more followers, the search area will display loading animation and then get removed from dom when complete
    # mutation observer detects these changes
    # if we scroll and the search loading animation does not come up, that means no new followers were loaded.
    # if after scrolling, we detect no mutations to the search input for more than x seconds, we know all followers are loaded.
    search_area_anchor_css: str = '[aria-label="Search input"], [aria-label="Search"]' 

    # represents each row containng information about the instagram user
    follower_item_css: str = (
        '[class="x1qnrgzn x1cek8b2 xb10e19 x19rwo8q x1lliihq x193iq5w xh8yej3"]'
    )

    # lets us know if the follower is a verified instagram user or not
    verified_bage_css: str = "[aria-label='Verified']"

    # used to fetch the follower username, link, and nickname of instagram follower
    follower_link_css: str = 'a[role="link"]'
    follower_name_css: str = (
        '.x1lliihq.x1plvlek.xryxfnj.x1n2onr6.xyejjpt.x15dsfln.x193iq5w.xeuugli.'
        'x1fj9vlw.x13faqbe.x1vvkbs.x1s928wv.xhkezso.x1gmr53x.x1cpjm7i.x1fgarty.'
        'x1943h6x.x1i0vuye.xvs91rp.xo1l8bm.x1roi4f4.x10wh9bi.xpm28yp.x8viiok.x1o7cslx'
    )
