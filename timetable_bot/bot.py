#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import collections

import telegram
import telegram.ext

from timetable_bot.handlers.simple_handlers import *
from timetable_bot.handlers.timetable import *
from timetable_bot.user_data import *

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)

    logger.info("Starting bot")

    logger.info("Loading user data...")
    user_data = load_user_data()
    if user_data is None:
        user_data = collections.defaultdict(dict)

    logger.info("Initializing bot...")
    with open("bot_token.txt") as f:
        updater = telegram.ext.Updater(f.read(), use_context=True)

    dp: telegram.ext.Dispatcher = updater.dispatcher
    dp.user_data.update(user_data)

    # TODO deadlines tracker
    # TODO other tasks tracker (e.g. buy batteries)
    dp.add_handler(start)
    dp.add_handler(help_command)
    dp.add_handler(admin_help)
    dp.add_handler(register_command)
    dp.add_handler(timetable)
    dp.add_handler(whole_timetable)
    dp.add_handler(add_lesson)
    dp.add_handler(remove_lesson)

    updater.start_polling()
    logger.info("Initializing done!")
    updater.idle()

    logger.info("Saving user data...")
    save_user_data(dp.user_data)


if __name__ == '__main__':
    main()
