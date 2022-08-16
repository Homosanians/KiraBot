import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")

IMAGES_PATH = './memes'
TRAIN_PATH = './train_dataset'
