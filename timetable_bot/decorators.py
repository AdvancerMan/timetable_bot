#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

import telegram
import telegram.ext

from timetable_bot.user_data import UserData

__all__ = ["bot_command", "for_registered_user"]
logger = logging.getLogger(__name__)


def bot_command(command_name=None):
    def decorator(command_handler):
        nonlocal command_name
        if command_name is None:
            command_name = command_handler.__name__

        def wrapper(update, context):
            logger.info(f"Handling /{command_name} command"
                        f" for {update.effective_user.id} user"
                        f" ({update.effective_user.full_name})")
            return command_handler(update, context)

        return wrapper

    return decorator


def for_registered_user(callback):
    def wrapper(update: telegram.Update, context: telegram.ext.CallbackContext):
        if context.user_data.get(UserData.IS_REGISTERED):
            return callback(update, context)
        else:
            update.message.reply_text("Sorry, you are not registered")
            return telegram.ext.ConversationHandler.END

    return wrapper
