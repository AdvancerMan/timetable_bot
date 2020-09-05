#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import enum
import pickle

__all__ = ["UserData", "load_user_data", "save_user_data"]
logger = logging.getLogger(__name__)
USER_DATA_FILE = "user_data.bin"


class UserData(enum.Enum):
    IS_REGISTERED = enum.auto


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
