from threading import Thread

from tqdm import tqdm

from scrapping.four_chan_scrapper import FourChanScrapper


def _threaded_scrapping():
    scrappers = [FourChanScrapper()]

    for scrapper in tqdm(scrappers):
        scrapper.get_images()
        print(f'Scrapped {scrapper.parsed} photos from {scrapper.name}')


def start_scrapping():
    print('Started scrapping images. Creating new thread.')
    thread = Thread(target=_threaded_scrapping)
    thread.start()
    thread.join()
    print("Scrapping complete. Thread is being terminated.")
