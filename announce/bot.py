import os
import random
import argparse
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, Filters, CommandHandler, CallbackQueryHandler
from announce import models

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


# ===============================


def capcha():
    wordlist = ["dog", "comb", "success", "messages", "sunlight"]
    return random.choice(wordlist)


def check(capcha, answer):
    return str(answer).strip() == str(len(capcha)).strip()


def chat(update, context):
    w = capcha()
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"""
Before you can join our chat group, we need to verify that you're a well
intentioned person and not a spam account.

To do that, please tell us how many characters are there in the word `{w}`.

Make sure that you reply to this message with a number and not a word. For
example, the word `list` has 4 letters in it and so you should reply with `4`.
    """,
    )


def error_callback(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def start(update, context):
    keyboard = []
    keyboard.append([InlineKeyboardButton("Join telegram group", callback_data="1")])
    keyboard.append([InlineKeyboardButton("Join event call", callback_data="2")])
    keyboard.append([InlineKeyboardButton("Get otp", callback_data="3")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="""Welcome to pyjaipur!

Please visit pyjaipur.org when you get the chance to see the latest of what's happening.

To join our community chat please reply with `/chat`.
        """,
        reply_markup=reply_markup,
    )


def callback_handler(update, context):
    query = update.callback_query
    query.answer()
    if query.data.startswith("cap."):
        _, cap, n = query.data.split(".")
        if check(cap, n):
            link = "https://t.me/joinchat/Egpy4xW1rgwAJpBXeTX66Q"
            context.bot.send_message(
                chat_id=update.effective_chat.id, text=f"Please join using: {link}"
            )
        else:
            context.bot.send_message(
                chat_id=update.effective_chat.id, text="Wrong answer."
            )
        return
    if query.data == "1":
        cap = capcha()
        keyboard = [
            [(lambda x: InlineKeyboardButton(x, callback_data=f"cap.{cap}.{x}"))(num)]
            for num in [str(random.choice(range(10))) for _ in range(3)]
            + [str(len(cap))]
        ]
        random.shuffle(keyboard)
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"How many letters are there in the word `{cap}`?",
            reply_markup=reply_markup,
        )
    elif query.data == "2":
        context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"Open pyjaipur.org/#call"
        )
    elif query.data == "3":
        session = models.Session()
        try:
            otp = models.Otp.loop_create(
                session, tg_handle=update.effective_user.username
            )
            context.bot.send_message(chat_id=update.effective_chat.id, text=otp.otp)
        finally:
            session.close()


def run():
    token = os.environ.get("TG_TOKEN")
    print(token)
    updater = Updater(token, use_context=True)
    updater.dispatcher.add_handler(CommandHandler("start", start, pass_user_data=True))
    updater.dispatcher.add_handler(
        CallbackQueryHandler(callback_handler, pass_user_data=True, pass_chat_data=True)
    )
    updater.start_polling()
    updater.idle()
