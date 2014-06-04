#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c)2013 Rackspace US, Inc.

# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from __future__ import print_function

import sys

def option_chooser(options, attr=None):
    """Given an iterable, enumerate its contents for a user to choose from.
    If the optional `attr` is not None, that attribute in each iterated
    object will be printed.

    This function will exit the program if the user chooses the escape option.
    """
    for num, option in enumerate(options):
        if attr:
            print("%s: %s" % (num, getattr(option, attr)))
        else:
            print("%s: %s" % (num, option))
    # Add an escape option
    escape_opt = num + 1
    print("%s: I want to exit!" % escape_opt)
    choice = raw_input("Selection: ")
    try:
        ichoice = int(choice)
        if ichoice > escape_opt:
            raise ValueError
    except ValueError:
        print("Valid entries are the numbers 0-%s. Received '%s'." % (escape_opt,
                choice))
        sys.exit()

    if ichoice == escape_opt:
        print("Bye!")
        sys.exit()

    return ichoice
