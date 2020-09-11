#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os

from timetable_bot.user_data import UserData
from timetable_bot.decorators import *
from timetable_bot.constants import *
from .timetable_util import *
from .conversation import *

__all__ = ["timetable", "whole_timetable",
           "add_lesson", "remove_lesson",
           "add_period", "remove_period"]
logger = logging.getLogger(__name__)


def get_nearest_time_periods(periods, now=None):
    # TODO timezone should be stored for each user
    if now is None:
        now = (datetime.datetime.now(datetime.timezone.utc) + TZ_UTC_OFFSET)
        now = now.time()
    answer = [period for period in periods if period[0] <= now <= period[1]]
    if len(answer) == 0:
        future_periods = [period for period in periods if now <= period[0]]
        nearest_period = min(future_periods, default=[None])[0]
        answer = [period for period in future_periods
                  if period[0] == nearest_period]
    return answer


@bot_command("table")
@for_registered_user
def timetable(update, context):
    # TODO even week or not
    day_of_week = datetime.date.today().weekday()
    today_table = context.user_data[UserData.TABLE][day_of_week]
    nearest_periods = get_nearest_time_periods(today_table.keys())

    if nearest_periods == [] \
            or len([period for period, lesson in today_table
                    if lesson is not None
                       and period[0] >= nearest_periods[0][0]]) == 0:
        day_of_week = (day_of_week + 1) % 7
        today_table = context.user_data[UserData.TABLE][day_of_week]
        nearest_periods = get_nearest_time_periods(
            today_table.keys(), datetime.time(0, 0, 0, 0)
        )

    update.message.reply_text(timetable_pretty_string(
        context, day_of_week, today_table, nearest_periods
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
    Questions.DAY_OF_WEEK, Questions.IS_EVEN_WEEK, Questions.TABLE_TIME_PERIOD,
    Questions.LESSON_SUBJECT, Questions.LESSON_TYPE,
    Questions.CLASSROOM, Questions.TEACHER,
    privileges_decorator=for_registered_user
)


def _remove_lesson(update, context, data):
    # TODO handle even/odd weeks
    day = context.user_data[UserData.TABLE][data[UserData.TABLE_DAY]]
    del day[data[UserData.TABLE_TIME]]


remove_lesson = create_conversation(
    "remove_lesson", _remove_lesson,
    Questions.DAY_OF_WEEK, Questions.IS_EVEN_WEEK, Questions.TABLE_TIME_PERIOD,
    privileges_decorator=for_registered_user
)


def _add_period(update, context, data):
    period = (data["period_start"], data["period_end"])
    user_periods = context.user_data[UserData.TABLE_DEFAULT_PERIODS]
    if period not in user_periods:
        user_periods.append(period)
        user_periods.sort()


class AskTimeQuestion(Question):
    def __init__(self, q_id, output_name):
        super(AskTimeQuestion, self).__init__(q_id, output_name)

    def parse_answer(self, answer):
        answer = super(AskTimeQuestion, self).parse_answer(answer)
        try:
            return datetime.time.fromisoformat(answer)
        except ValueError:
            return TgConvBadInput

    @property
    def bad_input_message(self):
        return super(AskTimeQuestion, self).bad_input_message() \
               + ", время должно быть в формате HH:MM"


add_period = create_conversation(
    "add_period", _add_period,
    AskTimeQuestion("period_start", "время начала в формате HH:MM"),
    AskTimeQuestion("period_end", "время конца в формате HH:MM"),
    privileges_decorator=for_registered_user
)


def _remove_period(update, context, data):
    period = data[UserData.TABLE_TIME]
    user_periods = context.user_data[UserData.TABLE_DEFAULT_PERIODS]
    if period in user_periods:
        user_periods.remove(period)


class ChooseDefaultUserPeriodQuestion(ChooseInRangeQuestion):
    def __init__(self, q_id, output_name):
        super(ChooseDefaultUserPeriodQuestion, self).__init__(
            q_id, output_name, [], []
        )

    def update(self, update, context):
        self.choices_names = [' - '.join((moment.strftime('%H:%M')
                                          for moment in period))
                              for period in
                              context.user_data[UserData.TABLE_DEFAULT_PERIODS]]
        self.choices = context.user_data[UserData.TABLE_DEFAULT_PERIODS]


remove_period = create_conversation(
    "remove_period", _remove_period,
    ChooseDefaultUserPeriodQuestion(UserData.TABLE_TIME,
                                    "период, который необходимо удалить"),
    privileges_decorator=for_registered_user
)
