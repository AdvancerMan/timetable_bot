#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from timetable_bot.decorators import *
from timetable_bot.utils import *
from timetable_bot.user_data import *
from .conversation import *

__all__ = ["help_command", "start", "admin_help", "register_command"]
logger = logging.getLogger(__name__)


def show_help(update, context):
    registered = context.user_data.get(UserData.IS_REGISTERED)
    update.message.reply_text(trim_indent(f"""
        Вы{" не" if not registered else ""} зарегистрированы

        /help - Вывести справку
        /admin_help - Вывести справку администратора
        /table - Расписание на ближайшие занятия
        /whole_table - Все расписание
        /add_lesson - Добавить урок в расписание
        /stop - Остановить введение данных (например, при добавлении урока)
    """))


@bot_command("help")
def help_command(update, context):
    show_help(update, context)


@bot_command("start")
def start(update, context):
    show_help(update, context)


@bot_command("admin_help")
@for_admin
def admin_help(update, context):
    show_help(update, context)
    update.message.reply_text(trim_indent(f"""
        /register - Зарегистрировать нового пользователя
    """))


def register_user(user_id, user_data):
    logger.info(f"Registering user {user_id}")
    if user_data.get(UserData.IS_REGISTERED):
        logger.info(f"User {user_id} was already registered")
        return
    user_data[UserData.IS_REGISTERED] = True
    user_data[UserData.IS_ADMIN] = False
    # FIXME bad code with hardcoded len
    user_data[UserData.TABLE] = [[None for _ in range(7)]  # len(table_periods)
                                 for _ in range(14)]


def _register(update, context, data):
    forward_from = data["user_message"].forward_from
    if forward_from is None:
        return TgConvBadInput
    user_id = forward_from.id
    user_data = context.dispatcher.user_data[user_id]
    register_user(user_id, user_data)


class _RegisterForwardQuestion(Question):
    def __init__(self):
        super(_RegisterForwardQuestion, self).__init__(
            "user_message",
            "сообщение пользователя, которого хотите добавить "
            "(перешлите любое его сообщение в этот чат)")

    def parse_answer(self, answer):
        return answer


register_command = create_conversation(
    "register", _register, _RegisterForwardQuestion(),
    privileges_decorator=for_admin
)
