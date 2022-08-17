import asyncio
import logging
import sys
from threading import Thread

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup

from core import strings, meme_provider, config, models, scheduler

bot = telebot.TeleBot(config.BOT_TOKEN)


def keyboard():
    markup = ReplyKeyboardMarkup(True, False)
    markup.add(KeyboardButton(strings.KEYBOARD_GET_MEME))
    return markup


def inline_keyboard(payload):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("👍", callback_data=f"meme_like:{payload}"),
               InlineKeyboardButton("👎", callback_data=f"meme_dislike:{payload}"))
    return markup


@bot.message_handler(commands=["start"])
def start(message):
    db_user = models.User(user_id=message.from_user.id)
    db_user.save()
    bot.send_message(message.chat.id, strings.START, reply_markup=keyboard())


@bot.message_handler(content_types=["text"])
def handle_text(message):
    if message.text == strings.KEYBOARD_GET_MEME:
        response = meme_provider.get_meme_image(message.from_user.id)
        if response.error:
            bot.send_message(message.chat.id, strings.REPLY_NO_MEMES_LEFT, reply_markup=keyboard())
        else:
            bot.send_chat_action(message.chat.id, 'upload_photo')
            bot.send_photo(message.chat.id, response.image,
                           reply_markup=inline_keyboard(f"{message.from_user.id}:{response.post_id}"))
    else:
        bot.send_message(message.chat.id, strings.REPLY_COMMAND_DOES_NOT_EXIST, reply_markup=keyboard())


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if "meme_like" in call.data:
        # Structure is call:user_id:post_id
        tg_user_id = call.data.split(':')[1]
        post_id = call.data.split(':')[2]
        db_user = models.User.get(models.User.user_id == tg_user_id)
        db_post = models.Post.get(models.Post.id == post_id)
        if not models.Assessment.select().where(models.Assessment.user == db_user).where(
                models.Assessment.post == db_post).exists():
            models.Assessment.create(post=db_post, user=db_user, positive=True)
        elif not models.Assessment.select().where(models.Assessment.user == db_user).where(
                models.Assessment.post == db_post).get().positive:
            db_assessment = models.Assessment.select().where(models.Assessment.user == db_user).where(
                models.Assessment.post == db_post).get()
            db_assessment.positive = True
            db_assessment.save()
            bot.answer_callback_query(call.id, strings.REPLY_ASSESSMENT_CHANGED)
        else:
            bot.answer_callback_query(call.id, strings.REPLY_CANNOT_RATE_TWICE)
    elif "meme_dislike" in call.data:
        tg_user_id = call.data.split(':')[1]
        post_id = call.data.split(':')[2]
        db_user = models.User.get(models.User.user_id == tg_user_id)
        db_post = models.Post.get(models.Post.id == post_id)
        if not models.Assessment.select().where(models.Assessment.user == db_user).where(
                models.Assessment.post == db_post).exists():
            models.Assessment.create(post=db_post, user=db_user, positive=False)
        elif models.Assessment.select().where(models.Assessment.user == db_user).where(
                models.Assessment.post == db_post).get().positive:
            db_assessment = models.Assessment.select().where(models.Assessment.user == db_user).where(
                models.Assessment.post == db_post).get()
            db_assessment.positive = False
            db_assessment.save()
            bot.answer_callback_query(call.id, strings.REPLY_ASSESSMENT_CHANGED)
        else:
            bot.answer_callback_query(call.id, strings.REPLY_CANNOT_RATE_TWICE)
    bot.answer_callback_query(call.id)


def get_severity_level():
    levels = {
        0: logging.DEBUG,
        1: logging.INFO,
        2: logging.WARNING,
        3: logging.ERROR,
        4: logging.FATAL
    }

    try:
        return levels[int(config.LOGGING_LEVEL)]
    except KeyError as e:
        raise ValueError('Undefined unit: {}'.format(e.args[0]))


if __name__ == '__main__':
    logging.basicConfig(filename='latest.log', encoding='utf-8', level=get_severity_level(),
                        format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    logging.debug('Warming up.')

    models.initialize()
    meme_provider.initialize()

    logging.debug('Allocating a thread for telegram\'s API infinite polling.')
    thread = Thread(target=bot.infinity_polling)
    thread.start()
    logging.info('Bot started.')

    asyncio.run(scheduler.run_coroutines())
