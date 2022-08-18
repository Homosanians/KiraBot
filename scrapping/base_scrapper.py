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

    # TODO Scanning each time is not efficient
    def get_unique_name(self):
        files = list(map(lambda x: os.path.basename(x), glob.glob(os.path.join(config.IMAGES_PATH, "*")))) + \
                list(map(lambda x: os.path.basename(x), glob.glob(os.path.join(config.PENDING_PATH, "*")))) + \
                list(map(lambda x: os.path.basename(x), glob.glob(os.path.join(config.TRAIN_PATH, "*"))))
        while True:
            unique_name = str(uuid.uuid4())
            if unique_name not in files:
                return unique_name
