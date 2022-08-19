import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
IMAGES_PATH = os.environ.get("IMAGES_PATH", './memes')
PENDING_PATH = os.environ.get("PENDING_PATH", './memes_pending')
TRAIN_PATH = os.environ.get("TRAIN_PATH", './dataset')

LOGGING_LEVEL = int(os.environ.get('LOGGING_LEVEL', 1))  # 0 - DEBUG, 1 - INFO, 2 - WARN, 3 - ERR, 4 - CRITICAL (FATAL)
ENABLE_SCRAPPING = int(os.environ.get('ENABLE_SCRAPPING', 1))
SCRAP_PERIOD_MINUTES = int(os.environ.get('SCRAP_PERIOD_MINUTES', 90))
MEME_SCAN_PERIOD_SECONDS = int(os.environ.get('MEME_SCAN_PERIOD_SECONDS', 30))
ROTATION_POST_LIFESPAN_HOURS = int(os.environ.get('ROTATION_POST_LIFESPAN_HOURS', 72))
ROTATION_KEEP_FILES_COUNT = int(os.environ.get('ROTATION_KEEP_FILES_COUNT', 10_000))

DUPLICATE_DETECT_THRESHOLD = float(int(os.environ.get('DUPLICATE_DETECT_THRESHOLD', 0.1)))  # 0 - absolute copy
