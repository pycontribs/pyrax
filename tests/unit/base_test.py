#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
import unittest


TIMING_FILE = ".testtimes.json"


class BaseTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(BaseTest, self).__init__(*args, **kwargs)
        self.timing = False
        # Create the output file if it doesn't exist
        with open(TIMING_FILE, "a") as jj:
            pass

    def setUp(self):
        if self.timing:
            self.begun = time.time()
        super(BaseTest, self).setUp()

    def tearDown(self):
        if self.timing:
            elapsed = time.time() - self.begun
            with open(TIMING_FILE, "r") as jj:
                try:
                    times = json.load(jj)
                except ValueError:
                    times = []
                times.append((elapsed, self._testMethodName))
            with open(TIMING_FILE, "w") as jj:
                json.dump(times, jj)
        super(BaseTest, self).tearDown()
