import logging

def make_logger(name: str, to_console: bool, level: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.handlers.clear()
    logger.propagate = False

    lvl = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(lvl)

    if to_console:
        h = logging.StreamHandler()
        h.setLevel(lvl)
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        h.setFormatter(fmt)
        logger.addHandler(h)
    else:
        # Prevent "No handler could be found" warnings
        logger.addHandler(logging.NullHandler())

    return logger
