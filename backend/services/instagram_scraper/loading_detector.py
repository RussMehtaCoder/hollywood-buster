# ----------------------------
# Loading Detector
# ----------------------------
import asyncio
from .config import Selectors
class LoadingDetector:
    """Polls for IG's loading graphic within a known row/container."""
    def __init__(self, selectors, cooldown_s: float = 0.1, logger=None) -> None:
        self.sel = selectors
        self.cooldown_s = cooldown_s
        self.log = logger

    async def poll_once(self, page):
        """
        Returns:
            True  -> loading exists now
            False -> loading does NOT exist now
            None  -> container missing / can't tell
        """
        try:
            row = await page.query_selector(self.sel.follower_row_css)
            if not row:
                if self.log:
                    pass
                    # self.log.debug("Loading row not found")
                return None
            loading_state = await row.query_selector(self.sel.loading_graphic_element)
            if self.log:
                self.log.debug(f"Loading graphic visible: {bool(loading_state)}")

            return loading_state is not None
        except Exception as e:
            if self.log:
                self.log.debug(f"Loading poll exception: {e}")
            return None

    async def wait_small(self) -> None:
        await asyncio.sleep(self.cooldown_s)
