#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import enum
import os
import datetime
import itertools

import telegram
import telegram.ext

from timetable_bot.user_data import UserData
from timetable_bot.decorators import *
from timetable_bot.utils import *

__all__ = ["create_add_event_handler", "timetable", "whole_timetable"]
logger = logging.getLogger(__name__)


class AddEventType(enum.Enum):
    DAY = enum.auto
    IS_EVEN = enum.auto
    TIME = enum.auto
    SUBJECT = enum.auto
    LESSON_TYPE = enum.auto
    CLASSROOM = enum.auto
    TEACHER = enum.auto


# TODO store periods for each user
table_periods = [
    (datetime.time(8, 20), datetime.time(9, 50)),
    (datetime.time(10, 0), datetime.time(11, 30)),
    (datetime.time(11, 40), datetime.time(13, 10)),
    (datetime.time(13, 30), datetime.time(15, 0)),
    (datetime.time(15, 20), datetime.time(16, 50)),
    (datetime.time(17, 0), datetime.time(18, 30)),
    (datetime.time(18, 40), datetime.time(20, 10)),
]

days_of_week = [
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье",
]

TZ_UTC_OFFSET = datetime.timedelta(hours=3)


def get_nearest_time_period_index():
    now = (datetime.datetime.now(datetime.timezone.utc) + TZ_UTC_OFFSET).time()
    future_periods = [period for period in table_periods if now <= period[1]]
    return table_periods.index(min(future_periods)) \
        if len(future_periods) != 0 else None


def timetable_pretty_string(context, day_of_week,
                            today_table=None, highlight_index=None):
    if today_table is None:
        today_table = context.user_data[UserData.TABLE][day_of_week]

    events = [f"{event[AddEventType.SUBJECT]} "
              f"[{event[AddEventType.CLASSROOM]}] "
              f"({event[AddEventType.LESSON_TYPE]}) - "
              f"{event[AddEventType.TEACHER]}"
              if event else '' for event in
              list(itertools.dropwhile(
                  lambda x: not x,
                  today_table[::-1]
              ))[::-1]]

    day = f"{days_of_week[day_of_week]}:"
    if len(events) == 0:
        return (os.linesep * 2).join([day, "Выходной"])
    else:
        return (os.linesep * 2).join([
            day,
            *[f"{'>>>>>>' if i == highlight_index else '-'}  "
              f"{table_periods[i][0].strftime('%H:%M')} - "
              f"{table_periods[i][1].strftime('%H:%M')} - {events[i]}"
              for i in range(len(events))]
        ])


@bot_command("table")
@for_registered_user
def timetable(update, context):
    # TODO even week or not
    day_of_week = datetime.date.today().weekday()
    nearest_index = get_nearest_time_period_index()
    today_table = context.user_data[UserData.TABLE][day_of_week]

    if nearest_index is None \
            or len([x for x in today_table[nearest_index:] if x]) == 0:
        day_of_week = (day_of_week + 1) % 7
        nearest_index = 0
        today_table = context.user_data[UserData.TABLE][day_of_week]

    update.message.reply_text(timetable_pretty_string(
        context, day_of_week, today_table, nearest_index
    ))


@bot_command("whole_table")
@for_registered_user
def whole_timetable(update, context):
    # TODO even week or not
    tables = [[s for s in timetable_pretty_string(context, i).splitlines() if s]
              for i in range(7)]
    update.message.reply_text(
        (os.linesep * 2).join(os.linesep.join(table) for table in tables)
    )


ud_choice = "__choice__"


def create_add_event_handlers():
    def last_handler(handler):
        def wrapper(update, context):
            handler(update, context)

            ud = context.user_data[ud_choice]
            day = (ud[AddEventType.DAY] + 6) % 7  # TODO even week or not
            time = ud[AddEventType.TIME] - 1

            context.user_data[UserData.TABLE][day][time] = {
                AddEventType.SUBJECT: ud[AddEventType.SUBJECT],
                AddEventType.LESSON_TYPE: ud[AddEventType.LESSON_TYPE],
                AddEventType.CLASSROOM: ud[AddEventType.CLASSROOM],
                AddEventType.TEACHER: ud[AddEventType.TEACHER],
            }

            logger.info(f"Successfully updated timetable"
                        f" for user {update.effective_user.id}")
            return stop_add_event(update, context)

        return wrapper

    return [
        create_question(
            AddEventType.DAY, AddEventType.IS_EVEN,
            "четность недели (0 - четная, 1 - нечетная, 2 - обе)",
            int, "значение должно быть в радиусе 0-7",
            lambda x: x in [str(x) for x in range(8)]
        ),

        create_question(
            AddEventType.IS_EVEN, AddEventType.TIME,
            trim_indent(
                "время урока:" + os.linesep + os.linesep +
                os.linesep.join(f"{i + 1} - {start.strftime('%H:%M')} - "
                                f"{end.strftime('%H:%M')}" for i, (start, end)
                                in zip(range(len(table_periods)),
                                       table_periods))
            ), int, "значение должно быть 0, 1 или 2",
            lambda x: x in [str(x) for x in range(3)]
        ),

        create_question(
            AddEventType.TIME, AddEventType.SUBJECT,
            "предмет по которому проводится урок", int,
            f"значение должно быть в радиусе 1-{len(table_periods)}",
            lambda x: x in [str(x) for x in range(1, len(table_periods) + 1)]
        ),

        create_question(
            AddEventType.SUBJECT, AddEventType.LESSON_TYPE,
            "тип урока (например, лабораторная или лекция)"
        ),

        create_question(
            AddEventType.LESSON_TYPE, AddEventType.CLASSROOM,
            "номер аудитории"
        ),

        create_question(
            AddEventType.CLASSROOM, AddEventType.TEACHER,
            "ФИО преподавателя"
        ),

        last_handler(create_question(AddEventType.TEACHER))
    ]


def create_add_event_handler():
    # FIXME renaming event --> lesson
    stop_handler = telegram.ext.CommandHandler('stop', stop_add_event)
    return telegram.ext.ConversationHandler(
        entry_points=[
            telegram.ext.CommandHandler('add_lesson', start_add_event)
        ],

        states={
            event_type: [
                stop_handler,
                telegram.ext.MessageHandler(telegram.ext.Filters.text, handler)
            ]
            for event_type, handler
            in zip(AddEventType, create_add_event_handlers())
        },

        fallbacks=[stop_handler],
    )


@bot_command("add_lesson")
@for_registered_user
def start_add_event(update, context):
    context.user_data[ud_choice] = {}
    update.message.reply_text(trim_indent("""
        Пожалуйста, введите день недели для урока:
        
        0 - Воскресенье
        1 - Понедельник
        2 - Вторник
        3 - Среда
        4 - Четверг
        5 - Пятница
        6 - Суббота
        7 - Опять воскресенье
    """))
    return AddEventType.DAY


@bot_command("stop")
def stop_add_event(update: telegram.Update, context):
    del context.user_data[ud_choice]
    update.message.reply_text("Изменение завершено!")
    return telegram.ext.ConversationHandler.END


def create_question(this_type, next_type=None, what_to_enter_next=None,
                    parse_data=lambda x: x, bad_data_message=None,
                    check_data=lambda *_: True):
    @message_handling_command(
        f"event addition ({AddEventType(this_type).name})"
    )
    def question(update: telegram.Update,
                 context: telegram.ext.CallbackContext):
        data = update.message.text

        good_data = check_data(data)
        logger.info(f"User {update.effective_user.id} passed"
                    f" {'good' if good_data else 'bad'} data")

        if not good_data:
            update.message.reply_text(f"ОШИБКА: {bad_data_message},"
                                      f" пожалуйста, не ошибайся")
            return this_type

        context.user_data[ud_choice][this_type] = parse_data(data)
        if next_type:
            update.message.reply_text(f"Пожалуйста, введите "
                                      f"{what_to_enter_next}")
            return next_type

    return question
