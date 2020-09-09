#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from timetable_bot.decorators import *
from timetable_bot.utils import *
from timetable_bot.user_data import *

__all__ = ["help_command", "register_user"]
logger = logging.getLogger(__name__)


@bot_command("help")
def help_command(update, context):
    update.message.reply_text(trim_indent(f"""
        Вы{
            " не" if not context.user_data.get(UserData.IS_REGISTERED) else ""
        } зарегистрированы

        /help - Вывести справку
        /table - Расписание на ближайшие занятия
        /whole_table - Все расписание
        /add_lesson - Добавить урок в расписание
        /stop - Остановить введение данных (например, при добавлении урока)
    """))


def register_user(user_id, user_data):
    logger.info(f"Registering user {user_id}")
    user_data[UserData.IS_REGISTERED] = True
    # FIXME bad code with hardcoded len
    user_data[UserData.TABLE] = [[None for _ in range(7)]  # len(table_periods)
                                 for _ in range(14)]
