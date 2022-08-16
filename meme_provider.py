import os
import random
from pathlib import Path
import glob

from meme_provider_response import MemeProviderResponse
from models import Post, View, User

DIRECTORY = './memes'


def refresh_database_memes():
    memes_paths = glob.glob(f"{DIRECTORY}/*.png") + glob.glob(f"{DIRECTORY}/*.jpg")
    for item in memes_paths:
        if not Post.select().where(Post.file_name == item).exists():
            Post.create(file_name=item, likes=0, dislikes=0)


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

    random_not_viewed_meme_path = random.choice(not_viewed_post_file_names)

    db_post = Post.select().where(Post.file_name == random_not_viewed_meme_path).get()
    print(db_post.id)
    if not os.path.exists(random_not_viewed_meme_path):
        db_post.delete_instance()
        return get_meme_image(user_id)

    View.create(post=db_post, user=db_user)
    with open(random_not_viewed_meme_path, 'rb') as image_file:
        image = image_file.read()
        error = image is None or db_post is None
        return MemeProviderResponse(error, image, db_post)


# Годные мемы перемещаются в папку для тренировки модели, затем все мемы удаляются.
def handle_outdated_memes(paths):
    # TODO
    for path in paths:
        os.remove(path)


def rotate_images_by_date(keep=1000):
    paths = sorted(Path(DIRECTORY).iterdir(), key=os.path.getmtime)
    paths.reverse()
    handle_outdated_memes(paths[keep:])


def init():
    if not os.path.exists(DIRECTORY):
        os.makedirs(DIRECTORY)
    refresh_database_memes()
    rotate_images_by_date()