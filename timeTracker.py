#!/usr/bin/python
# Copyright (c) Microsoft Corporation. All Rights Reserved.
# Licensed under the MIT license. See LICENSE file on the project webpage for details.

import datetime
from terminal import log

startTimes = dict() # key=uniqueStr, value=start.

def start_clock(message):
    log("running \"{}\" operation...".format(message), "")
    startTimes[message] = datetime.datetime.now()

def stop_clock(message):
    totalSeconds = datetime.datetime.now() - startTimes.pop(message)
    log("operation: \"{}\" complete".format(message),
        "took:      \"{}\" seconds".format(totalSeconds))
