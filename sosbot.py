#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram import ForceReply, ReplyKeyboardMarkup, KeyboardButton, ChatAction
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from dateutil import parser
from telegram.ext.dispatcher import run_async
from random import randint
import random
import logging
import bot_user
import datetime, time
import botan

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
job_queue = None

AWAITING_NAME, AWAITING_TYPE_USE, SOS_STATE, ADVICE_STATE, AWAITING_RESULT = range(5)

botan_token = "WJ9eIusq2:k:FhDuoG21Q64nVIcqyIYe"  # production

BOT_WELCOME = u"Привет! Я Миша. Моя задача-помочь тебе свалить со свидания, если оно стало скучным (SOS), или дать тебе полезный совет (Совет). Да. кстати, как я могу к тебе обращаться? Напиши 3 варианта своего имени в разных сообщениях"
BOT_TEXT_ME_SOS = u"думаешь, она окажется не в твоем вкусе, и вы не найдете общих тем для разговора? Или что-то уже пошло не так? В любом случае, я готов тебя вытащить из этой передряги, бро! Просто нажми SOS и я начну действовать уже через 5 минут. Или введи нужное время сам."
BOT_SOS_EXAMPLE = u"таймер установлен. Сообщение будет отправлено через 5 мин. Можете указать точное время, например: 21:45"

REPLY_MARKUP_SOS = u"SOS"
REPLY_MARKUP_ADVICE = u"Совет дня"
REPLY_MARKUP_ONE_MORE_ADVICE = u"Еще совет"

GLAD_TO_HELP = u"Рад, что помог"
SORRY_MAN = u"Соррян, чел. Сделал все, что в моих силах. Но я развиваюсь, и скоро в моем ассортименте появятся новые способы помочь тебе в тех или иных ситуациях."


def start(bot, update):


    bot_user.delete_user(update.message.chat_id)
    bot_user.new_user(update.message.chat_id)
    uid = update.message.from_user
    message_dict = update.message.to_dict()
    botan.track(botan_token, uid, message_dict, "/start")

    # bot.sendSticker(chat_id=update.message.chat_id, sticker="BQADAQADHAADyIsGAAFZfq1bphjqlgI")

    # if bot_user.get_names_len(update.message.chat_id) <= 3:
    #
    #     bot.sendMessage(update.message.chat_id,
    #                     text=BOT_WELCOME)
    #     bot_user.set_state(update.message.chat_id, AWAITING_NAME)
    # else:
    # reply_markup = ReplyKeyboardMarkup([[REPLY_MARKUP_SOS, REPLY_MARKUP_ADVICE]],
    #                                        one_time_keyboard=False,
    #                                        resize_keyboard=True)
    bot.sendMessage(update.message.chat_id,
                        text="Напиши 3 варианта своего имени, как к тебе обращаются друзья?")
    bot_user.set_state(update.message.chat_id, AWAITING_NAME)


def state_machine(bot, update):
    chat_id = update.message.chat_id
    text = update.message.text
    chat_state = bot_user.get_state(chat_id)


    if chat_state == AWAITING_NAME:
        bot_user.add_name(chat_id, text)
        if bot_user.get_names_len(chat_id) >= 3:
            reply_markup = ReplyKeyboardMarkup([[REPLY_MARKUP_SOS, REPLY_MARKUP_ADVICE]],
                                               one_time_keyboard=False,
                                               resize_keyboard=True)
            bot_user.set_state(chat_id, AWAITING_TYPE_USE)

            msgtext = bot_user.get_random_name(chat_id).decode("utf-8") + ", " + BOT_TEXT_ME_SOS
            bot.sendMessage(update.message.chat_id,
                        text=msgtext,
                        reply_markup=reply_markup)
        else:
            msgtext = u"Отлично " + bot_user.get_random_name(chat_id).decode("utf-8") + u". Введи еще " + str(3 - bot_user.get_names_len(chat_id))
            bot.sendMessage(update.message.chat_id,
                    text=msgtext)

    if chat_state == AWAITING_TYPE_USE:
        if text == REPLY_MARKUP_SOS:
            current_date = datetime.datetime.now()
            current_in_seconds = time.mktime(current_date.timetuple())

            bot_user.set_schedule(chat_id, current_in_seconds + 300)
            msgtext = bot_user.get_random_name(chat_id).decode("utf-8") + ", " + BOT_SOS_EXAMPLE
            bot.sendMessage(chat_id, text=msgtext)

        elif text == REPLY_MARKUP_ADVICE or text == REPLY_MARKUP_ONE_MORE_ADVICE:
            reply_markup = ReplyKeyboardMarkup([[REPLY_MARKUP_SOS, REPLY_MARKUP_ONE_MORE_ADVICE]],
                                               one_time_keyboard=False,
                                               resize_keyboard=True)
            msgtext = bot_user.get_random_advice().decode("utf-8")
            bot.sendMessage(update.message.chat_id,
                text=bot_user.get_random_advice(),
                reply_markup=reply_markup)

        else:

            try:
                schedule_date = parser.parse(text.decode("utf-8"))

                schedule_in_seconds = time.mktime(schedule_date.timetuple())
                current_date = datetime.datetime.now()
                current_in_seconds = time.mktime(current_date.timetuple())

                due = schedule_in_seconds - current_in_seconds

                if due < 0:
                    bot.sendMessage(update.message.chat_id,
                        text="Это уже прошлое, бро")
                else:
                    uid = update.message.from_user
                    message_dict = update.message.to_dict()
                    botan.track(botan_token, uid, message_dict, "Timer set")
                    bot_user.set_schedule(chat_id, schedule_in_seconds)
                    bot.sendMessage(chat_id, text='Таймер обновлен')

            except ValueError:
                bot.sendMessage(chat_id, text=u"Дружище, не понимаю что ты такое говоришь. Если что, то время задается так: 13:32 или 18:11")



    if chat_state == AWAITING_RESULT:
        if "да".decode("utf-8") in text or "Да".decode("utf-8") in text or "ага".decode("utf-8") in text or "Ага".decode("utf-8") in text or "угу".decode("utf-8") in text or "Угу".decode("utf-8") in text:
            bot.sendMessage(chat_id, text=GLAD_TO_HELP)
        else:
            bot.sendMessage(chat_id, text=SORRY_MAN)

        bot_user.set_state(chat_id, AWAITING_TYPE_USE)



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
    job_queue.put(alarm, 5, repeat=True)



def clear(bot, update):
    all_user = bot_user.all_users()
    if all_user is not False:
        for user in bot_user.all_users():
            print(user)
            bot.sendMessage(user,  text="user " + str(user) + " deleted")
            bot_user.delete_user(user)


@run_async
def alarm(bot):
    current_date = datetime.datetime.now()
    current_in_seconds = time.mktime(current_date.timetuple())
    for user in bot_user.all_users():
        if user is not False:
            if bot_user.get_schedule(user) is not None:
                schedule = float(bot_user.get_schedule(user))
                if schedule < current_in_seconds:
                    if schedule != 0:
                        bot_user.set_schedule(user, 0)
                        send_message(bot, user)



@run_async
def send_message(bot, user):
    text_row = bot_user.get_random_sos()
    msg = ""
    num_of_msg = 0

    for i, c in enumerate(text_row):
        if c != "|":
            msg += c
            if i == len(text_row) - 1:
                bot.sendChatAction(action=ChatAction.TYPING, chat_id=user)
                time.sleep(random.randint(7, 15))
                bot.sendMessage(user, text=msg)
        else:
            if num_of_msg == 0:
                text = bot_user.get_random_name(user) + ", " + msg
            else:
                text = msg
            bot.sendChatAction(action=ChatAction.TYPING, chat_id=user)
            time.sleep(random.randint(7, 15))
            bot.sendMessage(user, text=text)
            msg = ""
            num_of_msg += 1

    def ask_result(bot):
        bot.sendMessage(user, text="Все получилось?")
        bot_user.set_state(user, AWAITING_RESULT)

    job_queue.put(ask_result, 60 * 12, repeat=False)






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
    dp.add_handler(CommandHandler("clear", clear))
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