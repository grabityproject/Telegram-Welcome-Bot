#!/usr/bin/env python3
from telegram import Emoji, ParseMode, TelegramError, Update
from telegram.ext import Updater, MessageHandler, CommandHandler, Filters
from telegram.ext.dispatcher import run_async

import python3pickledb as pickledb

import configparser
from time import sleep
import traceback
import sys
from html import escape


# Configuration
CONFIG =  configparser.ConfigParser()
CONFIG.read("bot.conf")
BOTNAME = CONFIG.get("BOT","NAME")
TOKEN = CONFIG.get("BOT","TOKEN")
WELCOME_TEXT = open("welcome.txt").read()
HELP_TEXT = open("help.txt").read()


db = pickledb.load('bot.db', True)
if not db.get('chats'):
    db.set('chats', [])


@run_async
def send_async(bot, *args, **kwargs):
    bot.sendMessage(*args, **kwargs);

# Welcome a user to the chat
def welcome(bot, update):
    message = update.message
    chat_id = message.chat.id

    text = '%s\n\n%s' % ( WELCOME_TEXT, HELP_TEXT )
    text = text.replace('$fisrt_name',
                        message.new_chat_member.first_name)\
        .replace('$last_name', message.new_chat_member.last_name)\
        .replace('$title', message.chat.title)
    send_async(bot, chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN)


def linkMessage(bot, update):

    chat_id = update.message.chat.id
    chat_str = str(chat_id)
    if (not db.get(chat_str + '_quiet') or db.get(chat_str + '_adm') == update.message.from_user.id):
        send_async(bot, chat_id=chat_id,
                   text=HELP_TEXT,
                   parse_mode=ParseMode.MARKDOWN,
                   disable_web_page_preview=True)


def createMessage(bot, update):
    chats = db.get('chats')

    if update.message.chat.id not in chats:
        chats.append(update.message.chat.id)
        db.set('chats', chats)

    if update.message.new_chat_member is not None:
        return welcome(bot, update)


def error(bot, update, error, **kwargs):
    try:
        if isinstance(error, TelegramError)\
                and error.message == "Unauthorized"\
                or "PEER_ID_INVALID" in error.message\
                and isinstance(update, Update):

            chats = db.get('chats')
            chats.remove(update.message.chat_id)
            db.set('chats', chats)

        else:
            pass
            
    except:
        pass



def main():
    updater = Updater(TOKEN, workers=10)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("help", linkMessage))
    dp.add_handler(CommandHandler("resource", linkMessage))
    dp.add_handler(CommandHandler("link", linkMessage))

    dp.add_handler(MessageHandler([Filters.status_update], createMessage))

    dp.add_error_handler(error)
    update_queue = updater.start_polling(timeout=30, clean=False)

    updater.idle()

if __name__ == '__main__':
    main()
