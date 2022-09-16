import logging
import os
import random
from datetime import timedelta, datetime, timezone
from pathlib import Path
import glob

import tqdm as tqdm

from core import config, near_duplicate_detector
from core.meme_provider_response import MemeProviderResponse
from core.models import Post, View, User, Assessment
from core.near_duplicate_detector import NearDuplicateDetector
from scrapping import base_scrapper

dup_detector = None


# TODO Make this a class


def adopt_pending_memes():
    memes_paths = glob.glob(f"{config.PENDING_PATH}/*.png") + glob.glob(f"{config.PENDING_PATH}/*.jpg")

    if len(memes_paths) == 0:
        return

    logging.info(f'{len(memes_paths)} images pending adoption.')

    for path in tqdm.tqdm(memes_paths):
        try:
            filename = os.path.basename(path)
            signature = dup_detector.calculate_hash(path)
            if not dup_detector.is_duplicate(signature):
                if not Post.select().where(Post.file_name == filename).exists():
                    logging.debug(f'Creating a new DB Post model entry of {filename}, moving to storage.')
                    new_path = os.path.join(config.IMAGES_PATH, filename)
                    dup_detector.add(filename, signature)
                    os.rename(path, new_path)
                    Post.create(file_name=filename, hash=signature.tobytes())
                else:
                    logging.warning(f'Near duplicate is not detected however entry with same filename ({filename}) is '
                                    f'already occupied. Scrappers save files by uuid4 unique name with availability checks '
                                    f'so this is caused by moving files by hand. Generating a new name for the files.')
                    os.rename(path, os.path.join(config.PENDING_PATH, base_scrapper.get_unique_name()))
            else:
                logging.debug(f'Removing a pending image {filename} which is confirmed to be duplicate.')
                os.remove(path)
        except:
            logging.warning(f"Cannot adopt image, exception occurred. Deleting {path}.")
            os.remove(path)


def get_meme_image(user_id):
    if not User.select().where(User.user_id == user_id).exists():
        User.create(user_id=user_id)
    db_user = User.select().where(User.user_id == user_id).get()

    all_posts = [post for post in Post.select()]
    viewed_posts = [post for post in Post.select().join(View).join(User).where(View.user == db_user)]

    all_post_paths = []
    for post in all_posts:
        all_post_paths.append(post.file_name)

    viewed_post_paths = []
    for post in viewed_posts:
        viewed_post_paths.append(post.file_name)

    not_viewed_post_file_names = list(set(all_post_paths) - set(viewed_post_paths))

    # Checking no unviewed memes left
    if len(not_viewed_post_file_names) == 0:
        return MemeProviderResponse(True, None, None)

    random_not_viewed_meme_filename = random.choice(not_viewed_post_file_names)
    random_not_viewed_meme_path = os.path.join(config.IMAGES_PATH, random_not_viewed_meme_filename)

    db_post = Post.select().where(Post.file_name == random_not_viewed_meme_filename).get()

    if not os.path.exists(random_not_viewed_meme_path):
        logging.warning('Unrecommended action occurred. Some images were moved out from storage by hand.')
        db_post.delete_instance()
        return get_meme_image(user_id)

    View.create(post=db_post, user=db_user)
    with open(random_not_viewed_meme_path, 'rb') as image_file:
        image = image_file.read()
        error = image is None or db_post is None
        return MemeProviderResponse(error, image, db_post)


# Godniye memes moves to dataset train folder
def handle_outdated_memes(paths):
    logging.info('Outdated memes found. The purge process has started.')
    for path in paths:
        filename = os.path.basename(path)
        new_train_path = os.path.join(config.TRAIN_PATH, filename)
        if not os.path.exists(new_train_path):
            db_post = Post.get(Post.file_name == filename)
            likes = db_post.assessments.where(Assessment.positive == 1).count()
            dislikes = db_post.assessments.where(Assessment.positive == 0).count()
            views = db_post.views.count()

            dup_detector.remove(filename)
            db_post.delete_instance()
            os.rename(path, new_train_path)

            report_file_path = os.path.join(config.TRAIN_PATH, "data.csv")

            if not os.path.exists(report_file_path):
                with open(os.path.join(config.TRAIN_PATH, "data.csv"), "w", encoding="utf-8") as file:
                    file.write(f"filename,likes,dislikes,views\n")

            with open(os.path.join(config.TRAIN_PATH, "data.csv"), "a", encoding="utf-8") as file:
                file.write(f"{filename},{likes},{dislikes},{views}\n")
        else:
            logging.warning(f'User intervention detected. Cannot move file {filename} to train folder because a file '
                            f'with same name already exists there. Deleting files from {config.IMAGES_PATH}')
            dup_detector.remove(filename)
            Post.get(Post.file_name == filename).delete_instance()
            os.remove(path)


def rotate_memes(keep=1000, post_lifespan=timedelta(days=5)):
    # Moves last *keep* images to train folder, files csv entry and deletes from the DB.
    overflow_paths = sorted(Path(config.IMAGES_PATH).iterdir(), key=os.path.getmtime)
    overflow_paths.reverse()
    _, _, files = next(os.walk(os.path.normpath(config.IMAGES_PATH)))
    if len(files) > keep:
        handle_outdated_memes(overflow_paths[keep:])

    # Does the same with memes that present more than *post_lifespan* time.
    db_post = Post.select().where(Post.created_at < datetime.now(timezone.utc) - post_lifespan)
    overtime_paths = list(map(lambda x: os.path.join(config.IMAGES_PATH, x.file_name), db_post))
    # Confirm path exists to prevent FileNotFoundError when db entry exist but image by that path does not
    for path in overtime_paths:
        if not os.path.exists(path):
            logging.warning(f'Path to rotate images by exceeding time provided by the DB, '
                            f'but no file by that path was found in {config.IMAGES_PATH}')
            overtime_paths.remove(path)
    if len(overtime_paths) > 0:
        handle_outdated_memes(overtime_paths)


def initialize():
    if not os.path.exists(config.IMAGES_PATH):
        os.makedirs(config.IMAGES_PATH)
    if not os.path.exists(config.TRAIN_PATH):
        os.makedirs(config.TRAIN_PATH)
    if not os.path.exists(config.PENDING_PATH):
        os.makedirs(config.PENDING_PATH)

    global dup_detector
    dup_detector = NearDuplicateDetector()

    logging.info('Importing hashes to duplicate detector from the DB.')
    for post in tqdm.tqdm(Post.select()):
        filename = post.file_name
        hash_bytes = post.hash
        dup_detector.add(filename, near_duplicate_detector.bytes_to_signature(hash_bytes))

    adopt_pending_memes()
