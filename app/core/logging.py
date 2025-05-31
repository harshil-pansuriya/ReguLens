from loguru import logger
import sys

def setup_logging():
    logger.remove()
    logger.add(sys.stderr, format="{time} | {level} | {message}", level="INFO")
    logger.add("logs/app.log", rotation="1 MB", retention="10 days", level="DEBUG")