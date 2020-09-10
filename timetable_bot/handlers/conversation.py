#!/usr/bin/env python
# -*- coding: utf-8 -*-

import telegram
import telegram.ext

import os
import logging

from timetable_bot.decorators import *
from timetable_bot.user_data import *
from timetable_bot.constants import *

__all__ = ["create_conversation", "Questions"]
logger = logging.getLogger(__name__)


class TgConvBadInput:
    pass


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


ud_choice = "__choice__"


def _create_questions_handler(q1, q2, handle_chosen_data, stop_conversation):
    @message_handling_command(f"question ({q1.q_id})")
    def handler(update: telegram.Update, context: telegram.ext.CallbackContext):
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
            handle_chosen_data(update, context, context.user_data[ud_choice])
            return stop_conversation.callback(update, context)

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

    states = {}
    for q1, q2 in zip(questions, [*questions[1:], None]):
        states[q1.q_id] = [telegram.ext.MessageHandler(
            telegram.ext.Filters.text & ~telegram.ext.Filters.command,
            _create_questions_handler(q1, q2, handle_chosen_data,
                                      stop_conversation)
        )]

    return telegram.ext.ConversationHandler(
        entry_points=[start_conversation],
        states=states,
        fallbacks=[stop_conversation],
    )


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
