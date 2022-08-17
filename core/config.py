import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")

IMAGES_PATH = './memes'
TRAIN_PATH = './dataset'
SCRAP_PERIOD_MINUTES = 60
ROTATION_POST_LIFESPAN_HOURS = 72
ROTATION_KEEP_FILES_COUNT = 1000
