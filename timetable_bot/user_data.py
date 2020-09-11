#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import enum
import pickle

__all__ = ["UserData", "load_user_data", "save_user_data"]
logger = logging.getLogger(__name__)
USER_DATA_FILE = "user_data.bin"


class UserData(enum.Enum):
    IS_REGISTERED = 1
    TABLE = 2
    IS_ADMIN = 3

    TABLE_DAY = 4
    TABLE_IS_EVEN = 5
    TABLE_TIME = 6
    TABLE_SUBJECT = 7
    TABLE_LESSON_TYPE = 8
    TABLE_CLASSROOM = 9
    TABLE_TEACHER = 10
    TABLE_DEFAULT_PERIODS = 11


def load_user_data():
    try:
        with open(USER_DATA_FILE, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        logger.error("User data file was not found")
        return None


def save_user_data(user_data):
    with open(USER_DATA_FILE, 'wb') as f:
        pickle.dump(user_data, f, pickle.HIGHEST_PROTOCOL)
