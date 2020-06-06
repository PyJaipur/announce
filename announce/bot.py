import os
import random
import argparse
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, Filters, CommandHandler, CallbackQueryHandler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


# ===============================
intro = """\
Hello!

PyJaipur is a community of students and working professionals in Jaipur.

- We use telegram for our chat.
- pyjaipur.org is our website.
- We have a presence on lot of social platforms. Subscribe to any of them to receive updates about events. Alternatively you could also just join the telegram group.

**Rules for chat**

1. No promotional links in the main chat group. Please use the links group for that.
2. Be polite. In text conversations, the way you say a sentence is lost so normal things can appear rude.
3. When asking a question, please follow dontasktoask.com
"""


def capcha():
    wordlist = ["dog", "comb", "success", "messages", "sunlight"]
    return random.choice(wordlist)


def check(capcha, answer):
    return str(answer).strip() == str(len(capcha)).strip()


def start(update, context):
    keyboard = []
    keyboard.append([InlineKeyboardButton("PyJaipur intro", callback_data="intro")])
    keyboard.append(
        [InlineKeyboardButton("Join telegram group", callback_data="joingroup")]
    )
    keyboard.append([InlineKeyboardButton("Join event call", callback_data="livecall")])
    keyboard.append([InlineKeyboardButton("Get otp", callback_data="getotp")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="""Welcome to pyjaipur! What would you like to do?""",
        reply_markup=reply_markup,
    )


def callback_handler(update, context):
    query = update.callback_query
    query.answer()
    if query.data == "intro":
        context.bot.send_message(chat_id=update.effective_chat.id, text=intro)
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
    if query.data == "joingroup":
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
    elif query.data == "livecall":
        context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"Open pyjaipur.org/#call"
        )
    elif query.data == "getotp":
        if update.effective_user.username is None:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Please set your username in order to receive an otp",
            )
        else:
            from announce import models

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
