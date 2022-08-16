import glob
import os
import uuid

from core import config


class BaseScrapper:
    def __init__(self):
        self.name = 'Scrapper'
        self.parsed = 0

    def get_images(self):
        pass

    def get_unique_name(self):
        files = list(map(lambda x: os.path.basename(x), glob.glob(os.path.join(config.IMAGES_PATH, "*"))))
        while True:
            unique_name = str(uuid.uuid4())
            if unique_name not in files:
                return unique_name
