import itertools
import os

from timetable_bot.constants import *
from timetable_bot.user_data import *


__all__ = ["timetable_pretty_string", "get_sorted_table_periods",
           "datetime_now"]


def timetable_pretty_string(context, day_of_week,
                            today_table=None, highlight_periods=None,
                            cut_suffix=True):
    if today_table is None:
        today_table = context.user_data[UserData.TABLE][day_of_week]
    if highlight_periods is None:
        highlight_periods = []

    today_table = [(period, today_table.get(period, None)) for period
                   in get_sorted_table_periods(context.user_data,
                                               today_table=today_table)]
    useful_periods = list(itertools.dropwhile(
        lambda item: cut_suffix and item[1] is None, today_table[::-1]
    ))[::-1]

    lessons = [f"{'>>>>>>' if (start, end) in highlight_periods else '-'}  "
               f"{start.strftime('%H:%M')} - "
               f"{end.strftime('%H:%M')} - "
               + (f"{lesson[UserData.TABLE_SUBJECT]} "
                  f"[{lesson[UserData.TABLE_CLASSROOM]}] "
                  f"({lesson[UserData.TABLE_LESSON_TYPE]}) - "
                  f"{lesson[UserData.TABLE_TEACHER]}"
                  if lesson is not None else '')
               for (start, end), lesson in useful_periods]

    if len(lessons) == 0:
        lessons = ["Выходной"]
    return (os.linesep * 2).join([f"{days_of_week[day_of_week]}:", *lessons])


def get_sorted_table_periods(user_data, today_table=None, day_of_week=None):
    if today_table is None:
        if day_of_week is None:
            raise ValueError("both (today_table, day_of_week) "
                             "should not be None")
        today_table = user_data[UserData.TABLE][day_of_week]
    elif day_of_week is not None:
        raise ValueError("one of (today_table, day_of_week) should be None")

    # TODO is_even
    return list(sorted({
        *today_table.keys(),
        *user_data[UserData.DEFAULT_PERIODS]
    }))


def datetime_now(utc_offset=datetime.timedelta()):
    return datetime.datetime.now(datetime.timezone.utc) + utc_offset
