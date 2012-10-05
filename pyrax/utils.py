#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import tempfile


class SelfDeletingTempfile(object):
    name = None

    def __enter__(self):
        fd, self.name = tempfile.mkstemp()
        os.close(fd)
        return self.name

    def __exit__(self, type, value, traceback):
        os.unlink(self.name)
