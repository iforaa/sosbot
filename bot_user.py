import redis
import random

from random import randint

NAMES = "_names"
STATE = "_state"
SOSS = "_soss"
ADVICES = "_advices"
SCHEDULE = "_schedule"

red = redis.StrictRedis(host='localhost', port=6379, db=1)


def is_user_new(chat_id):
    chat_id = str(chat_id)
    if red.get(chat_id + "_chat_id") is None:
        return True
    else:
        return False


def all_users():
    if len(red.keys(pattern="*_chat_id")) > 0:
        return red.mget(red.keys(pattern="*_chat_id"))
    return False


def delete_user(chat_id):
    chat_id = str(chat_id)
    red.delete(chat_id + "_chat_id")
    red.delete(chat_id + NAMES)


def get_state(chat_id):
    chat_id = str(chat_id)
    return int(red.get(chat_id + STATE))


def set_state(chat_id, state):
    chat_id = str(chat_id)
    red.set(chat_id + STATE, state)


def new_user(chat_id):
    chat_id = str(chat_id)
    red.set(chat_id + "_chat_id", chat_id)


def set_schedule(chat_id, seconds):
    chat_id = str(chat_id)
    red.set(chat_id + SCHEDULE, seconds)


def get_schedule(chat_id):
    chat_id = str(chat_id)
    return red.get(chat_id + SCHEDULE)


def add_name(chat_id, name):
    chat_id = str(chat_id)
    red.rpush(chat_id + NAMES, name)


def get_names_len(chat_id):
    chat_id = str(chat_id)
    names = red.lrange(chat_id + NAMES, 0, -1)
    return len(names)


def show_names(chat_id):
    chat_id = str(chat_id)
    names = red.lrange(chat_id + NAMES, 0, -1)
    text = ""
    i = 1
    for word in phrases:
        text += str(i) + ") `" + word + "`\n"
        i += 1

    return text


def get_random_name(chat_id):
    chat_id = str(chat_id)
    phrases = red.lrange(chat_id + NAMES, 0, -1)
    if len(phrases) > 0:
        return phrases[random.randint(0, len(phrases) - 1)]
    else:
        return "Empty"


def get_random_sos():
    phrases = red.lrange(SOSS, 0, -1)
    if len(phrases) > 0:
        return phrases[random.randint(0, len(phrases) - 1)]
    else:
        return "Empty"


def add_sos_phrase(phrase):
    red.rpush(SOSS, phrase)


def show_all_sos_phrases():
    phrases = red.lrange(SOSS, 0, -1)
    text = ""
    i = 1
    for word in phrases:
        text += str(i) + ") `" + word + "`\n"
        i += 1

    return text


def remove_sos_phrase(num):
    element = red.lindex(SOSS, num - 1)
    red.lrem(PHRASES, -1, element)


def get_random_advice():
    phrases = red.lrange(ADVICES, 0, -1)
    if len(phrases) > 0:
        return phrases[random.randint(0, len(phrases) - 1)]
    else:
        return "Empty"


def add_advice_phrase(phrase):
    red.rpush(ADVICES, phrase)


def show_all_advice_phrases():
    phrases = red.lrange(ADVICES, 0, -1)
    text = ""
    i = 1
    for word in phrases:
        text += str(i) + ") `" + word + "`\n"
        i += 1

    return text


def remove_advice_phrase(num):
    element = red.lindex(ADVICES, num - 1)
    red.lrem(ADVICES, -1, element)
