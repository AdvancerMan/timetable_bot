#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

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
        user_data = {}

    logger.info("Initializing bot...")
    with open("bot_token.txt") as f:
        updater = telegram.ext.Updater(f.read(), use_context=True)

    dp: telegram.ext.Dispatcher = updater.dispatcher
    dp.user_data.update(user_data)

    dp.add_handler(telegram.ext.CommandHandler('help', help_command))
    dp.add_handler(telegram.ext.CommandHandler('table', timetable))
    dp.add_handler(create_add_event_handler())

    updater.start_polling()
    logger.info("Initializing done!")
    updater.idle()

    logger.info("Saving user data...")
    save_user_data(dp.user_data)


if __name__ == '__main__':
    main()
