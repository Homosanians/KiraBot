import os
import random
from pathlib import Path
import glob

from core import config
from core.meme_provider_response import MemeProviderResponse
from core.models import Post, View, User


def refresh_database_memes():
    memes_paths = glob.glob(f"{config.IMAGES_PATH}/*.png") + glob.glob(f"{config.IMAGES_PATH}/*.jpg")
    for item in memes_paths:
        if not Post.select().where(Post.file_name == item).exists():
            filename = os.path.basename(item)
            Post.create(file_name=filename, likes=0, dislikes=0)


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
    print(len(not_viewed_post_file_names))

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


# Godniye memes moves to dataset train folder
# TODO
# Handle every start, by time. Move and delete
def handle_outdated_memes(paths):
    # check for duplications among filenames
    # append csv file in train folder where stored likes, dislikes, filename
    for path in paths:
        filename = os.path.basename(path)
        new_train_path = os.path.join(config.TRAIN_PATH, filename)
        if not os.path.exists(new_train_path):
            os.rename(path, new_train_path)
            with open(os.path.join(config.TRAIN_PATH, "data.csv"), "a") as file:
                file.write(f"{filename},{0},{0}")
        else:
            print('WARNING Cannot move file to train folder because a file with same name already exists there.')


def rotate_images_by_date(keep=1000):
    paths = sorted(Path(config.IMAGES_PATH).iterdir(), key=os.path.getmtime)
    paths.reverse()
    handle_outdated_memes(paths[keep:])


def init():
    if not os.path.exists(config.IMAGES_PATH):
        os.makedirs(config.IMAGES_PATH)
    refresh_database_memes()
    rotate_images_by_date()
