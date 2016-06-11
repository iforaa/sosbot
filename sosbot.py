#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram import ForceReply, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from dateutil import parser
from telegram.ext.dispatcher import run_async

import logging
import bot_user
import datetime, time


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
job_queue = None

AWAITING_NAME, AWAITING_TYPE_USE, SOS_STATE, ADVICE_STATE = range(4)


BOT_WELCOME = u"Привет! Я Миша. Моя задача-помочь тебе свалить со свидания, если оно стало скучным (SOS), или дать тебе полезный совет (Совет). Да. кстати, как я могу к тебе обращаться? Напиши 3 варианта своего имени в разных сообщениях"
BOT_TEXT_ME_SOS = u"Думаешь, она окажется не в твоем вкусе, и вы не найдете общих тем для разговора? Или что-то уже пошло не так? В любом случае, я готов тебя вытащить из этой передряги, бро! Просто положи телефон и я начну действовать уже через 5 минут. Или введи нужное время сам."
BOT_SOS_EXAMPLE = 'Таймер установлен. Сообщение будет отправлено через 5 мин. Можете указать точное время. Например: 21:45'

REPLY_MARKUP_SOS = u"SOS"
REPLY_MARKUP_ADVICE = u"Совет дня"
REPLY_MARKUP_ONE_MORE_ADVICE = u"Еще совет"


def start(bot, update):
    reply_markup = ReplyKeyboardMarkup([[REPLY_MARKUP_SOS, REPLY_MARKUP_ADVICE]],
                                       one_time_keyboard=False,
                                       resize_keyboard=True)

    if bot_user.get_names_len(update.message.chat_id) < 3:
        bot.sendMessage(update.message.chat_id,
                        text=BOT_WELCOME,
                        reply_markup=reply_markup)
        bot_user.set_state(update.message.chat_id, AWAITING_NAME)
    else:
        bot.sendMessage(update.message.chat_id,
                        text="Здравствуйте " + bot_user.get_random_name(),
                        reply_markup=reply_markup)
        bot_user.set_state(update.message.chat_id, AWAITING_NAME)


def state_machine(bot, update):
    chat_id = update.message.chat_id
    text = update.message.text
    chat_state = bot_user.get_state(chat_id)

    if chat_state == AWAITING_NAME:
        bot_user.add_name(chat_id, text)

        if bot_user.get_names_len(chat_id) >= 3:
            bot_user.set_state(chat_id, AWAITING_TYPE_USE)
            bot.sendMessage(update.message.chat_id,
                        text=BOT_TEXT_ME_SOS)
        else:
            bot.sendMessage(update.message.chat_id,
                    text="Еще одно")

    if chat_state == AWAITING_TYPE_USE:
        if text == REPLY_MARKUP_SOS:
            current_date = datetime.datetime.now()
            current_in_seconds = time.mktime(current_date.timetuple())

            bot_user.set_schedule(chat_id, current_in_seconds + 300)
            bot.sendMessage(chat_id, text=BOT_SOS_EXAMPLE)

        elif text == REPLY_MARKUP_ADVICE or text == REPLY_MARKUP_ONE_MORE_ADVICE:
            reply_markup = ReplyKeyboardMarkup([[REPLY_MARKUP_SOS, REPLY_MARKUP_ONE_MORE_ADVICE]],
                                               one_time_keyboard=False,
                                               resize_keyboard=True)
            bot.sendMessage(update.message.chat_id,
                text=bot_user.get_random_advice(),
                reply_markup=reply_markup)

        else:
            schedule_date = parser.parse(text)
            schedule_in_seconds = time.mktime(schedule_date.timetuple())
            current_date = datetime.datetime.now()
            current_in_seconds = time.mktime(current_date.timetuple())

            due = schedule_in_seconds - current_in_seconds

            if due < 0:
                bot.sendMessage(update.message.chat_id,
                                text="Это уже прошлое, бро")
            else:
                bot_user.set_schedule(chat_id, schedule_in_seconds)
                bot.sendMessage(chat_id, text='Таймер обновлен')



def addadvice(bot, update, args):
    text = ""
    for arg in args:
        text += arg
        text += " "

    bot_user.add_advice_phrase(text)


def removeadvice(bot, update, args):
    bot_user.remove_advice_phrase(int(args[0]))


def showadvice(bot, update):
    bot.sendMessage(update.message.chat_id, text=bot_user.show_all_advice_phrases())



def addsos(bot, update, args):
    text = ""
    for arg in args:
        text += arg
        text += " "

    bot_user.add_sos_phrase(text)


def removesos(bot, update, args):
    bot_user.remove_sos_phrase(int(args[0]))


def showsos(bot, update):
    bot.sendMessage(update.message.chat_id, text=bot_user.show_all_sos_phrases())


def restart(bot, update):
    job_queue.put(alarm, 10, repeat=True)


@run_async
def alarm(bot):
    current_date = datetime.datetime.now()
    current_in_seconds = time.mktime(current_date.timetuple())

    for user in bot_user.all_users():
        schedule = int(bot_user.get_schedules(user))
        if schedule < current_in_seconds:
            if schedule != 0:
                bot.sendMessage(user, text=bot_user.get_random_name(user) + ", " + bot_user.get_random_sos())
                bot_user.set_schedule(user, 0)


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def main():
    global job_queue

    updater = Updater("211360109:AAFRKMTfPAkKlDzlf31zvZQ79quEqtTe_nQ")
    job_queue = updater.job_queue

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("addsos", addsos, removesos, pass_args=True))
    dp.add_handler(CommandHandler("showsos", showsos))
    dp.add_handler(CommandHandler("removesos", removesos, pass_args=True))
    dp.add_handler(CommandHandler("addadvice", addadvice, removesos, pass_args=True))
    dp.add_handler(CommandHandler("showadvice", showadvice))
    dp.add_handler(CommandHandler("removeadvice", removeadvice, pass_args=True))
    dp.add_handler(CommandHandler("restart", restart))

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", start))
    # dp.add_handler(CommandHandler("sos", sos, pass_args = True))
    dp.add_handler(MessageHandler([Filters.text], state_machine))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Block until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()