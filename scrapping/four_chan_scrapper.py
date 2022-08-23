import os
import uuid

import requests
from bs4 import BeautifulSoup

from core import config
from scrapping.base_scrapper import BaseScrapper

URL_ADDRESS = 'https://boards.4chan.org/b/'


class FourChanScrapper(BaseScrapper):
    def __init__(self):
        super().__init__()
        self.name = '4chan'

    def parse(self, url):
        result = requests.get(url)

        if result.status_code != 200:
            raise Exception('Status code is not 200.')

        soup = BeautifulSoup(result.content, features="html.parser")

        elements = soup.select('a')

        for element in elements:
            if '.jpg' in element['title'] or '.png' in element['title']:
                image_url = f"https:{element['href']}"
                img_data = requests.get(image_url).content

                with open(f'{os.path.join(config.IMAGES_PATH, get_unique_name())}.jpg', 'wb') as handler:
                    handler.write(img_data)
                    self.parsed += 1

    def get_images(self):
        self.parse(URL_ADDRESS)
        for i in range(2, 11):
            self.parse(URL_ADDRESS + str(i))
