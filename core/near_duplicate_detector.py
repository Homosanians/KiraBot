import logging
import os

import numpy
from image_match.goldberg import ImageSignature

from core import config


def signature_to_bytes(signature):
    return signature.tobytes()


def bytes_to_signature(bytes_data):
    return numpy.ndarray((648,), numpy.int8, bytes_data)


class NearDuplicateDetector:
    def __init__(self):
        self.data = {}  # filename, signature
        self.gis = ImageSignature()

    # Names Include and Exclude is more appropriate imho
    def add(self, path):
        filename = os.path.basename(path)
        if filename in self.data:
            logging.error(f'Cannot add new image. {path} is already registered.')
        self.data[filename] = self.gis.generate_signature(path)

    def add(self, path, signature):
        filename = os.path.basename(path)
        if filename in self.data:
            logging.error(f'Cannot add new image. {path} is already registered.')
        self.data[filename] = signature

    def remove(self, path):
        filename = os.path.basename(path)
        if filename not in self.data:
            logging.error(f'Cannot remove an image. {path} is not registered.')
        else:
            self.data.pop(filename)

    def calculate_hash(self, path):
        return self.gis.generate_signature(path)

    def is_duplicate(self, signature):
        #  Get key by value
        #if signature == list(self.data.keys())[list(self.data.values()).index(signature)]:
        #    return True

        #  Iterate all images in memory and one that pass the proximity threshold
        for key, value in self.data.items():
            if self.gis.normalized_distance(signature, value) < config.DUPLICATE_DETECT_THRESHOLD:
                return True

        return False
