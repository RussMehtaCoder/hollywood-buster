class WheelEventScroller:

    def __init__(self, logger=None) -> None:
        self.log = logger

    # emits a scroll event in the follower list window to force all followers to load
    async def scroll(self, page, selectors, delta_y: int) -> None:

        if self.log:
            self.log.debug(f"Scrolling through followers list {selectors.scroll_container_css} by {delta_y}")

        await page.evaluate(
            """
            ([sel, dy]) => {
                const el = document.querySelector(sel);
                if (!el) return;
                el.dispatchEvent(new WheelEvent('wheel', {deltaY: dy, bubbles: true, cancelable: true}));
                el.scrollBy({ top: dy, behavior: 'smooth' });
            }
            """,
            [selectors.scroll_container_css, delta_y],
        )
