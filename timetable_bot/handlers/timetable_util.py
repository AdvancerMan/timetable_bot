import itertools
import os

from timetable_bot.constants import *
from timetable_bot.user_data import UserData


__all__ = ["timetable_pretty_string"]


def timetable_pretty_string(context, day_of_week,
                            today_table=None, highlight_periods=None,
                            cut_suffix=True):
    if today_table is None:
        today_table = context.user_data[UserData.TABLE][day_of_week]
    if highlight_periods is None:
        highlight_periods = []

    default_periods = context.user_data[UserData.TABLE_DEFAULT_PERIODS]
    today_table = sorted([(period, today_table.get(period, None)) for period
                          in {*today_table.keys(), *default_periods}])
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
