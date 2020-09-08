#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from timetable_bot.decorators import *
from timetable_bot.utils import *
from timetable_bot.user_data import *

__all__ = ["help_command"]
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
