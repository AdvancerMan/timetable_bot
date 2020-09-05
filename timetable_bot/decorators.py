#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

import telegram
import telegram.ext

from timetable_bot.user_data import UserData

__all__ = ["message_handling_command", "bot_command", "for_registered_user"]
logger = logging.getLogger(__name__)


def message_handling_command(what_to_handle=""):
    def decorator(handler):
        def wrapper(update: telegram.Update, context):
            logger.info(f"Handling {what_to_handle},"
                        f" message: [{update.message.text}]"
                        f" for {update.effective_user.id} user"
                        f" ({update.effective_user.full_name})")
            return handler(update, context)

        return wrapper

    return decorator


def bot_command(command_name):
    return message_handling_command("/%s command" % command_name)


with open("registered_users.txt") as f:
    registered_users = [int(line.strip()) for line in f.read().splitlines()]


def register_user(user, user_data):
    logger.info(f"Registering user {user.id} ({user.full_name})")
    user_data[UserData.IS_REGISTERED] = True
    # FIXME bad code with hardcoded len
    user_data[UserData.TABLE] = [[None for _ in range(7)]  # len(table_periods)
                                 for _ in range(14)]


def for_registered_user(callback):
    def wrapper(update: telegram.Update, context: telegram.ext.CallbackContext):
        registered = context.user_data.get(UserData.IS_REGISTERED)

        if not registered and update.effective_user.id in registered_users:
            register_user(update.effective_user, context.user_data)
            registered = True

        if registered:
            return callback(update, context)
        else:
            update.message.reply_text("Sorry, you are not registered")
            return telegram.ext.ConversationHandler.END

    return wrapper
