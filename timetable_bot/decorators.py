#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

import telegram
import telegram.ext

from timetable_bot.user_data import UserData

__all__ = ["message_handling_command", "bot_command",
           "for_registered_user", "for_admin"]
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
    def decorator(handler):
        return telegram.ext.CommandHandler(
            command_name,
            message_handling_command("/%s command" % command_name)(handler)
        )

    return decorator


def for_user_group(group_flag, group_name):
    def decorator(callback):
        def wrapper(update, context, *args, **kwargs):
            if context.user_data.get(group_flag):
                return callback(update, context, *args, **kwargs)
            else:
                logger.info(f"User {update.effective_user.id} "
                            f"is not in {group_flag} group")
                update.message.reply_text(f'Прости, ты не состоишь в группе '
                                          f'"{group_name}"(')
                return telegram.ext.ConversationHandler.END

        return wrapper

    return decorator


for_registered_user = for_user_group(UserData.IS_REGISTERED,
                                     "зарегистрированные")

for_admin = for_user_group(UserData.IS_ADMIN, "админы")
