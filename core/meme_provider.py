import logging
import os
import random
from datetime import timedelta, datetime, timezone
from pathlib import Path
import glob

from core import config
from core.meme_provider_response import MemeProviderResponse
from core.models import Post, View, User, Assessment


def refresh_database_memes():
    memes_paths = glob.glob(f"{config.IMAGES_PATH}/*.png") + glob.glob(f"{config.IMAGES_PATH}/*.jpg")
    for item in memes_paths:
        filename = os.path.basename(item)
        if not Post.select().where(Post.file_name == filename).exists():
            Post.create(file_name=filename)


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
        db_post.delete_instance()
        return get_meme_image(user_id)

    View.create(post=db_post, user=db_user)
    with open(random_not_viewed_meme_path, 'rb') as image_file:
        image = image_file.read()
        error = image is None or db_post is None
        return MemeProviderResponse(error, image, db_post)


def handle_duplications():
    # TODO
    pass


# Godniye memes moves to dataset train folder
def handle_outdated_memes(paths):
    logging.debug('Outdated memes found. The purge process has started.')
    for path in paths:
        filename = os.path.basename(path)
        new_train_path = os.path.join(config.TRAIN_PATH, filename)
        if not os.path.exists(new_train_path):
            os.rename(path, new_train_path)

            db_post = Post.select().where(Post.id == 4).get()
            likes = db_post.assessments.where(Assessment.positive == 1).count()
            dislikes = db_post.assessments.where(Assessment.positive == 0).count()
            views = db_post.views.count()

            with open(os.path.join(config.TRAIN_PATH, "data.csv"), "a") as file:
                file.write(f"{filename},{likes},{dislikes},{views}\n")
        else:
            logging.warning(f'Cannot move file {filename} to train folder because a file with same name already exists '
                  f'there.')


def rotate_memes(keep=1000, post_lifespan=timedelta(days=5)):
    # Moves last *keep* images to train folder, files csv entry and deletes from the DB.
    overflow_paths = sorted(Path(config.IMAGES_PATH).iterdir(), key=os.path.getmtime)
    overflow_paths.reverse()
    if len(overflow_paths) > 0:
        handle_outdated_memes(overflow_paths[keep:])

    # Does the same with memes that present more than *post_lifespan* time.
    db_post = Post.select().where(Post.created_at < datetime.now(timezone.utc) - post_lifespan)
    overtime_paths = list(map(lambda x: os.path.join(config.IMAGES_PATH, x.file_name), db_post))
    if len(overtime_paths) > 0:
        handle_outdated_memes(overtime_paths)


def initialize():
    if not os.path.exists(config.IMAGES_PATH):
        os.makedirs(config.IMAGES_PATH)
    if not os.path.exists(config.TRAIN_PATH):
        os.makedirs(config.TRAIN_PATH)
    refresh_database_memes()
