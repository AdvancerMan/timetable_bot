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

    with open("registered_users.txt") as f:
        registered_users = [int(line.strip()) for line in f.read().splitlines()]

    for user_id in registered_users:
        if not user_data[user_id].get(UserData.IS_REGISTERED):
            register_user(user_id, user_data[user_id])

    logger.info("Initializing bot...")
    with open("bot_token.txt") as f:
        updater = telegram.ext.Updater(f.read(), use_context=True)

    dp: telegram.ext.Dispatcher = updater.dispatcher
    dp.user_data.update(user_data)

    # TODO deadlines tracker
    # TODO other tasks tracker (e.g. buy batteries)
    dp.add_handler(telegram.ext.CommandHandler('help', help_command))
    dp.add_handler(telegram.ext.CommandHandler('start', help_command))
    dp.add_handler(telegram.ext.CommandHandler('table', timetable))
    dp.add_handler(telegram.ext.CommandHandler('whole_table', whole_timetable))
    dp.add_handler(create_add_event_handler())

    updater.start_polling()
    logger.info("Initializing done!")
    updater.idle()

    logger.info("Saving user data...")
    save_user_data(dp.user_data)


if __name__ == '__main__':
    main()
