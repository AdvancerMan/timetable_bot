#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

__all__ = ["trim_indent"]


def trim_indent(s):
    return os.linesep.join(s.lstrip() for s in s.splitlines())
