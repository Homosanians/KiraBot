import os
import uuid

import praw as praw
import requests
from bs4 import BeautifulSoup

from core import config
from scrapping.base_scrapper import BaseScrapper, get_unique_name


class RedditScrapper(BaseScrapper):
    def __init__(self):
        super().__init__()
        self.name = 'reddit'
        self.subreddits = ['memes', 'cursedimages', 'cursedmemes']
        self.reddit = praw.Reddit(client_id=config.REDDIT_CLIENT_ID, client_secret=config.REDDIT_CLIENT_SECRET,
                                  user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36')

    def get_images(self):
        for subreddit in self.subreddits:
            hot_posts = self.reddit.subreddit(subreddit).top(time_filter="week", limit=50)
            for post in hot_posts:
                img_data = requests.get(post.url).content
                with open(f'{os.path.join(config.PENDING_PATH, get_unique_name())}.jpg', 'wb') as handler:
                    handler.write(img_data)
                    self.parsed += 1
