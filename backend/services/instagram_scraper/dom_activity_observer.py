class DomActivityObserver:
    """
    Attaches a Mutation Observer to a given HTML element. 
    """
    def __init__(self, quiet_ms: int, logger=None) -> None:
        self.quiet_ms = quiet_ms
        self.log = logger
    """
    Attaches a Mutation Observer to a given HTML element. 
    This is used to detect inactivity within the Instagram Follower list.
    If the scrolling event does not produce more followers (aka mutation) in the dom for a prolonged period, then likely the full follower list has been loaded.
    In such cases, that indicates we do not need to scroll anymore. however, if we detect activity after scroll, lazy loading is not complete. 
    Marks the DOM as 'quiet' after no mutations for `quiet_ms`.
    Exposes is_stable() to check if the dom has been stable for X amount of seconds.
    """
    async def start(self, page, anchor_selector: str) -> None:
        if self.log:
            self.log.debug(f"Starting DOM observer on search element: {anchor_selector}")

        await page.evaluate(
            """({selector, quietMs}) => {
                window.__domActivityQuietDone = false;
                const target = document.querySelector(selector) || document.body;

                let timeout;
                const observer = new MutationObserver(() => {
                    console.log("Mutation(s) detected:");
                    clearTimeout(timeout);
                    timeout = setTimeout(() => {
                    console.log('No mutation detected after time');
                        observer.disconnect();
                        window.__domActivityQuietDone = true;
                    }, quietMs);
                });

                observer.observe(target, {
                    childList: true,
                    subtree: true,
                    attributes: true,
                    characterData: true
                });

                // fallback: if element does not exist then trivally the dom is quiet
                timeout = setTimeout(() => {
                 console.log(' No changes detected after timeout, stopped watching.');
                    observer.disconnect();
                    window.__domActivityQuietDone = true;
                }, quietMs);
            }""",
            {"selector": anchor_selector, "quietMs": self.quiet_ms},
        )

    async def is_stable(self, page) -> bool:
        # check the global context to see if the dom activity is quiet
        return await page.evaluate("() => Boolean(window.__domActivityQuietDone)")
