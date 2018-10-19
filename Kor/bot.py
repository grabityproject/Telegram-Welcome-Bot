#!/usr/bin/env python3
import configparser
import logging
from time import sleep
import traceback
import sys
from html import escape

from telegram import Emoji, ParseMode, TelegramError, Update
from telegram.ext import Updater, MessageHandler, CommandHandler, Filters
from telegram.ext.dispatcher import run_async

import python3pickledb as pickledb

# Configuration
CONFIG =  configparser.ConfigParser()
CONFIG.read("bot.conf")
BOTNAME = CONFIG.get("BOT","NAME")
TOKEN = CONFIG.get("BOT","TOKEN")
WELCOME_TEXT = open("welcome.txt").read()
HELP_TEXT = open("help.txt").read()


# Create database object
db = pickledb.load('bot.db', True)

if not db.get('chats'):
    db.set('chats', [])

# Set up logging
root = logging.getLogger()
root.setLevel(logging.INFO)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)


@run_async
def send_async(bot, *args, **kwargs):
    bot.sendMessage(*args, **kwargs);

# Welcome a user to the chat
def welcome(bot, update):
    """ Welcomes a user to the chat """

    message = update.message
    chat_id = message.chat.id
    logger.info('%s joined to chat %d (%s)'
                 % (escape(message.new_chat_member.last_name),
                    chat_id,
                    escape(message.chat.title)))

    # Pull the custom message for this chat from the database
    text = db.get(str(chat_id))

    # Use default message if there's no custom one set

    text = '%s\n\n%s' % ( WELCOME_TEXT, HELP_TEXT )

    # Replace placeholders and send message
    text = text.replace('$fisrt_name',
                        message.new_chat_member.first_name)\
        .replace('$last_name', message.new_chat_member.last_name)\
        .replace('$title', message.chat.title)
    send_async(bot, chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN)


def linkMessage(bot, update):

    chat_id = update.message.chat.id
    chat_str = str(chat_id)
    if (not db.get(chat_str + '_quiet') or db.get(chat_str + '_adm') ==
            update.message.from_user.id):
        send_async(bot, chat_id=chat_id,
                   text=HELP_TEXT,
                   parse_mode=ParseMode.MARKDOWN,
                   disable_web_page_preview=True)


def empty_message(bot, update):
    """
    Empty messages could be status messages, so we check them if there is a new
    group member, someone left the chat or if the bot has been added somewhere.
    """

    # Keep chatlist
    chats = db.get('chats')

    if update.message.chat.id not in chats:
        chats.append(update.message.chat.id)
        db.set('chats', chats)
        logger.info("I have been added to %d chats" % len(chats))

    if update.message.new_chat_member is not None:
        # Bot was added to a group chat
        return welcome(bot, update)


def error(bot, update, error, **kwargs):
    """ Error handling """

    try:
        if isinstance(error, TelegramError)\
                and error.message == "Unauthorized"\
                or "PEER_ID_INVALID" in error.message\
                and isinstance(update, Update):

            chats = db.get('chats')
            chats.remove(update.message.chat_id)
            db.set('chats', chats)
            logger.info('Removed chat_id %s from chat list'
                        % update.message.chat_id)
        else:
            logger.error("An error (%s) occurred: %s"
                         % (type(error), error.message))
    except:
        pass



def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN, workers=10)

    # # Get the dispatcher to register handlers
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("help", linkMessage))
    dp.add_handler(CommandHandler("resource", linkMessage))
    dp.add_handler(CommandHandler("link", linkMessage))

    dp.add_handler(MessageHandler([Filters.status_update], empty_message))

    dp.add_error_handler(error)

    update_queue = updater.start_polling(timeout=30, clean=False)

    updater.idle()

if __name__ == '__main__':
    main()
