#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import enum
import os
import datetime

import telegram
import telegram.ext

from timetable_bot.user_data import UserData
from timetable_bot.decorators import *
from timetable_bot.utils import *

__all__ = ["create_add_event_handler", "timetable", "whole_timetable"]
logger = logging.getLogger(__name__)


class AddEventType(enum.Enum):
    DAY = 0
    IS_EVEN = 1
    TIME = 2
    SUBJECT = 3
    LESSON_TYPE = 4
    CLASSROOM = 5
    TEACHER = 6


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
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


@bot_command("table")
@for_registered_user
def timetable(update, context, day_of_week=None):
    # TODO even week or not
    if day_of_week is None:
        day_of_week = datetime.date.today().weekday()
    today_table = context.user_data[UserData.TABLE][day_of_week]

    events = [f"{event[AddEventType.SUBJECT]} "
              f"[{event[AddEventType.CLASSROOM]}] "
              f"({event[AddEventType.LESSON_TYPE]}) - "
              f"{event[AddEventType.TEACHER]}"
              if event else 'No event'
              for event in today_table]

    double_linesep = os.linesep * 2
    update.message.reply_text(double_linesep.join([
        f"{days_of_week[day_of_week]}:",
        *[f"-  {period[0]} - {period[1]} - {event}"
          for period, event in zip(table_periods, events)]
    ]))


@bot_command("whole_table")
@for_registered_user
def whole_timetable(update, context):
    # TODO even week or not
    for i in range(7):
        timetable(update, context, i)


def create_add_event_handlers():
    def last_handler(handler):
        def wrapper(update, context):
            handler(update, context)

            ud = context.user_data["add_event"]
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
            "on which weeks lesson is (0 - even, 1 - odd, 2 - both)",
            int, "value should be in range 0-7",
            lambda x: x in [str(x) for x in range(8)]
        ),

        create_question(
            AddEventType.IS_EVEN, AddEventType.TIME,
            trim_indent(
                "time of the lesson:" + os.linesep + os.linesep +
                os.linesep.join(f"{i + 1} - {start} - {end}" for i, (start, end)
                                in zip(range(len(table_periods)),
                                       table_periods))
            ), int, "value should be 0, 1 or 2",
            lambda x: x in [str(x) for x in range(3)]
        ),

        create_question(
            AddEventType.TIME, AddEventType.SUBJECT,
            "subject of the lesson", int,
            f"value should be in range 1-{len(table_periods)}",
            lambda x: x in [str(x) for x in range(1, len(table_periods) + 1)]
        ),

        create_question(
            AddEventType.SUBJECT, AddEventType.LESSON_TYPE,
            "lesson type (might be lab or lection)"
        ),

        create_question(
            AddEventType.LESSON_TYPE, AddEventType.CLASSROOM,
            "classroom for the lesson"
        ),

        create_question(
            AddEventType.CLASSROOM, AddEventType.TEACHER,
            "lesson teacher"
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


@bot_command("add_event")
@for_registered_user
def start_add_event(update, context):
    context.user_data["add_event"] = {}
    update.message.reply_text(trim_indent("""
        Please, enter day of week for your lesson:
        
        0 - Sunday
        1 - Monday
        2 - Tuesday
        3 - Wednesday
        4 - Thursday
        5 - Friday
        6 - Saturday
        7 - Sunday again
    """))
    return AddEventType.DAY


@bot_command("stop")
def stop_add_event(update: telegram.Update, context):
    del context.user_data["add_event"]
    update.message.reply_text("Ended changing timetable!")
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
            update.message.reply_text(f"Error: {bad_data_message},"
                                      f" please, retry")
            return this_type

        context.user_data["add_event"][this_type] = parse_data(data)
        if next_type:
            update.message.reply_text(f"Please, enter {what_to_enter_next}")
            return next_type

    return question
