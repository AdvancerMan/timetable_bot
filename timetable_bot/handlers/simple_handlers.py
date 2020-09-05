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
    update.message.reply_markdown(trim_indent(f"""
        You are{
            " not" if not context.user_data.get(UserData.IS_REGISTERED) else ""
        } registered

        /table - Your timetable
    """))
