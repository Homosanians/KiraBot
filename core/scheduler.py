import asyncio
import logging
from asyncio import sleep
from datetime import timedelta

from core import config
from core.meme_provider import refresh_database_memes, rotate_memes, handle_duplications
from services import scrapping_service


async def __rotation_coroutine():
    while True:
        logging.debug('Rotation coroutine initiated.')
        refresh_database_memes()
        rotate_memes(keep=config.ROTATION_KEEP_FILES_COUNT,
                     post_lifespan=timedelta(hours=config.ROTATION_POST_LIFESPAN_HOURS))
        handle_duplications()
        await sleep(config.MEME_SCAN_PERIOD_SECONDS)


async def __scraping_coroutine():
    if config.ENABLE_SCRAPPING != 1:
        return
    while True:
        logging.debug('Scraping coroutine initiated.')
        scrapping_service.start_scrapping()
        await sleep(config.SCRAP_PERIOD_MINUTES)


async def run_coroutines():
    logging.debug('Scheduler started issuing tasks.')
    await asyncio.gather(
        __rotation_coroutine(),
        __scraping_coroutine()
    )
