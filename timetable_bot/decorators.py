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
        def wrapper(update, context, *args, **kwargs):
            logger.info(f"Handling {what_to_handle},"
                        f" message: [{update.message.text}]"
                        f" for {update.effective_user.id} user"
                        f" ({update.effective_user.full_name})")
            return handler(update, context, *args, **kwargs)

        return wrapper

    return decorator


def bot_command(command_name):
    return message_handling_command("/%s command" % command_name)


def for_registered_user(callback):
    def wrapper(update, context, *args, **kwargs):
        if context.user_data.get(UserData.IS_REGISTERED):
            return callback(update, context, *args, **kwargs)
        else:
            logger.info(f"User {update.effective_user.id} is not registered")
            update.message.reply_text("Прости, ты не зарегистрирован(")
            return telegram.ext.ConversationHandler.END

    return wrapper
