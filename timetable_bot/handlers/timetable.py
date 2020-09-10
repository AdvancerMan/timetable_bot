#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import datetime
import itertools

import telegram
import telegram.ext

from timetable_bot.user_data import UserData
from timetable_bot.decorators import *

__all__ = ["create_conversation", "timetable",
           "whole_timetable", "add_lesson",
           "Questions"]
logger = logging.getLogger(__name__)


class TgConvBadInput:
    pass


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

    events = [f"{event[UserData.TABLE_SUBJECT]} "
              f"[{event[UserData.TABLE_CLASSROOM]}] "
              f"({event[UserData.TABLE_LESSON_TYPE]}) - "
              f"{event[UserData.TABLE_TEACHER]}"
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


# FIXME renaming event --> lesson
def add_lesson(update, context, choices):
    day = choices[UserData.TABLE_DAY]  # TODO even week or not
    time = choices[UserData.TABLE_TIME]

    del choices[UserData.TABLE_DAY]
    del choices[UserData.TABLE_TIME]
    del choices[UserData.TABLE_IS_EVEN]
    context.user_data[UserData.TABLE][day][time] = choices

    logger.info(f"Successfully updated timetable"
                f" for user {update.effective_user.id}")


class Question:
    def __init__(self, q_id, output_name):
        self.q_id = q_id
        self.output_name = output_name

    def update(self, update, context):
        pass

    def parse_answer(self, answer):
        return answer

    @property
    def input_prompt(self):
        return f"Пожалуйста, введите, {self.output_name}"

    @property
    def bad_input_message(self):
        return "ОШИБКА, пожалуйста, не ошибайся"


class ChooseInRangeQuestion(Question):
    def __init__(self, q_id, output_name, choices, choices_names):
        super().__init__(q_id, output_name)
        self.choices = choices
        self.choices_names = choices_names

    def parse_answer(self, answer):
        return self.choices[int(answer) - 1] \
            if answer in [str(x) for x in self.range] else TgConvBadInput

    @property
    def range(self):
        return range(1, len(self.choices) + 1)

    @property
    def pretty_choices(self):
        return os.linesep * 2 \
               + os.linesep.join(f"{i} - {choice}"
                                 for i, choice in zip(self.range,
                                                      self.choices_names))

    @property
    def input_prompt(self):
        return super(ChooseInRangeQuestion, self).input_prompt \
               + self.pretty_choices

    @property
    def bad_input_message(self):
        return super(ChooseInRangeQuestion, self).bad_input_message \
               + ", вот тебе еще раз подсказка:" + self.pretty_choices


class Questions:
    DAY_OF_WEEK = ChooseInRangeQuestion(
        UserData.TABLE_DAY, "день недели", range(7), days_of_week
    )

    IS_EVEN_WEEK = ChooseInRangeQuestion(
        UserData.TABLE_IS_EVEN, "четность недели", range(3),
        ["нечетная", "четная", "обе"]
    )

    TIME_PERIOD = ChooseInRangeQuestion(
        UserData.TABLE_TIME, "время", range(len(table_periods)),
        [f"{period[0].strftime('%H:%M')} - {period[1].strftime('%H:%M')}"
         for period in table_periods]
    )

    LESSON_SUBJECT = Question(UserData.TABLE_SUBJECT, "предмет урока")

    LESSON_TYPE = Question(UserData.TABLE_LESSON_TYPE,
                           "тип урока (например, лабораторная или лекция)")

    CLASSROOM = Question(UserData.TABLE_CLASSROOM, "номер аудитории")

    TEACHER = Question(UserData.TABLE_TEACHER, "ФИО учителя")


ud_choice = "__choice__"


def create_questions_handler(q1, q2, handle_chosen_data, stop_conversation):
    @message_handling_command(f"event addition ({q1.q_id})")
    def handler(update: telegram.Update,
                context: telegram.ext.CallbackContext):
        q1.update(update, context)

        data = q1.parse_answer(update.message.text)
        is_bad_data = data is TgConvBadInput

        logger.info(f"User {update.effective_user.id} passed"
                    f" {'bad' if is_bad_data else 'good'} data")
        if is_bad_data:
            update.message.reply_text(q1.bad_input_message)
            return q1.q_id

        context.user_data[ud_choice][q1.q_id] = data

        if q2 is not None:
            q2.update(update, context)
            update.message.reply_text(q2.input_prompt)
            return q2.q_id
        else:
            handle_chosen_data(update, context,
                               context.user_data[ud_choice])
            return stop_conversation(update, context)

    return handler


def create_conversation(start_command, handle_chosen_data,
                        first_question, *questions):
    questions = [first_question, *questions]

    @bot_command(start_command)
    @for_registered_user
    def start_conversation(update, context):
        context.user_data[ud_choice] = {}
        first_question.update(update, context)
        update.message.reply_text(first_question.input_prompt)
        return first_question.q_id

    @bot_command("stop")
    def stop_conversation(update, context):
        del context.user_data[ud_choice]
        update.message.reply_text("Спасибо, что вы с нами!")
        return telegram.ext.ConversationHandler.END

    handlers = {}
    for q1, q2 in zip(questions, [*questions[1:], None]):
        handlers[q1.q_id] = [telegram.ext.MessageHandler(
            telegram.ext.Filters.text & ~telegram.ext.Filters.command,
            create_questions_handler(q1, q2, handle_chosen_data,
                                     stop_conversation)
        )]

    return telegram.ext.ConversationHandler(
        entry_points=[
            telegram.ext.CommandHandler(start_command, start_conversation)
        ],
        states=handlers,
        fallbacks=[telegram.ext.CommandHandler("stop", stop_conversation)],
    )
