import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup

from core import strings, meme_provider, config, models
from scrapping import scrapping_service

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
        # call:user_id:post_id
        tg_user_id = call.data.split(':')[1]
        post_id = call.data.split(':')[2]
        db_user = models.User.get(models.User.user_id == tg_user_id)
        db_post = models.Post.get(models.Post.id == post_id)
        if not models.Assessment.select().where(models.Assessment.post == db_post).exists():
            models.Assessment.create(post=db_post, user=db_user, positive=True)
        elif not models.Assessment.get(models.Assessment.post == db_post).positive:
            db_assessment = models.Assessment.get(user=db_user)
            db_assessment.positive = True
            db_assessment.save()
        else:
            bot.answer_callback_query(call.id, strings.REPLY_CANNOT_RATE_TWICE)
    elif "meme_dislike" in call.data:
        tg_user_id = call.data.split(':')[1]
        post_id = call.data.split(':')[2]
        db_user = models.User.get(models.User.user_id == tg_user_id)
        db_post = models.Post.get(models.Post.id == post_id)
        if not models.Assessment.select().where(models.Assessment.post == db_post).exists():
            models.Assessment.create(post=db_post, user=db_user, positive=False)
        elif models.Assessment.get(models.Assessment.post == db_post).positive:
            db_assessment = models.Assessment.get(user=db_user)
            db_assessment.positive = False
            db_assessment.save()
        else:
            bot.answer_callback_query(call.id, strings.REPLY_CANNOT_RATE_TWICE)
    bot.answer_callback_query(call.id)


models.init()
meme_provider.init()
#scrapping_service.start_scrapping()
bot.infinity_polling()
