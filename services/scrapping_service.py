import logging
from threading import Thread

from scrapping.four_chan_scrapper import FourChanScrapper

scrappers = [FourChanScrapper()]


def __threaded_scrapping(scrapper):
    logging.debug(f'Scrapper {scrapper.name} started gathering images.')
    scrapper.get_images()
    logging.debug(f'Scrapped {scrapper.parsed} photos from {scrapper.name}.')


def start_scrapping():
    logging.info('Scrappers thread allocation started.')
    for scrapper in scrappers:
        thread = Thread(target=__threaded_scrapping, args=[scrapper])
        thread.start()
