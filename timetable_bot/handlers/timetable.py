#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import itertools

from timetable_bot.user_data import UserData
from timetable_bot.decorators import *
from timetable_bot.constants import *
from .conversation import *

__all__ = ["timetable", "whole_timetable", "add_lesson", "remove_lesson"]
logger = logging.getLogger(__name__)


def get_nearest_time_period_index():
    now = (datetime.datetime.now(datetime.timezone.utc) + TZ_UTC_OFFSET).time()
    future_periods = [period for period in table_periods if now <= period[1]]
    return table_periods.index(min(future_periods)) \
        if len(future_periods) != 0 else None


def timetable_pretty_string(context, day_of_week,
                            today_table=None, highlight_index=None):
    if today_table is None:
        today_table = context.user_data[UserData.TABLE][day_of_week]

    lessons = [f"{lesson[UserData.TABLE_SUBJECT]} "
               f"[{lesson[UserData.TABLE_CLASSROOM]}] "
               f"({lesson[UserData.TABLE_LESSON_TYPE]}) - "
               f"{lesson[UserData.TABLE_TEACHER]}"
               if lesson else '' for lesson in
               list(itertools.dropwhile(
                   lambda x: not x,
                   today_table[::-1]
               ))[::-1]]

    day = f"{days_of_week[day_of_week]}:"
    if len(lessons) == 0:
        return (os.linesep * 2).join([day, "Выходной"])
    else:
        return (os.linesep * 2).join([
            day,
            *[f"{'>>>>>>' if i == highlight_index else '-'}  "
              f"{table_periods[i][0].strftime('%H:%M')} - "
              f"{table_periods[i][1].strftime('%H:%M')} - {lessons[i]}"
              for i in range(len(lessons))]
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


def _add_lesson(update, context, choices):
    day = choices[UserData.TABLE_DAY]  # TODO even week or not
    time = choices[UserData.TABLE_TIME]

    del choices[UserData.TABLE_DAY]
    del choices[UserData.TABLE_TIME]
    del choices[UserData.TABLE_IS_EVEN]
    context.user_data[UserData.TABLE][day][time] = choices

    logger.info(f"Successfully updated timetable"
                f" for user {update.effective_user.id}")


add_lesson = create_conversation(
    "add_lesson", _add_lesson,
    Questions.DAY_OF_WEEK, Questions.IS_EVEN_WEEK, Questions.TIME_PERIOD,
    Questions.LESSON_SUBJECT, Questions.LESSON_TYPE,
    Questions.CLASSROOM, Questions.TEACHER,
    privileges_decorator=for_registered_user
)


def _remove_lesson(update, context, data):
    # TODO handle even/odd weeks
    day = context.user_data[UserData.TABLE][data[UserData.TABLE_DAY]]
    day[data[UserData.TABLE_TIME]] = None


remove_lesson = create_conversation(
    "remove_lesson", _remove_lesson,
    Questions.DAY_OF_WEEK, Questions.IS_EVEN_WEEK, Questions.TIME_PERIOD,
    privileges_decorator=for_registered_user
)
