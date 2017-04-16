#!/usr/bin/python
# Copyright (c) Microsoft Corporation. All Rights Reserved.
# Licensed under the MIT license. See LICENSE file on the project webpage for details.

import os
from terminal import local_shell_wrapper
from timeTracker import *

def source_settings():
    timingNotification="get shared settings"
    start_clock(timingNotification)

    # Directory of this python file.
    scriptDir = os.path.dirname(os.path.realpath(__file__))

    bashFileName =      "getLocalGitInfo.sh"
    settingsFileName =  "settings.sh"
    localSettingsPath = os.path.join(scriptDir, settingsFileName)

    # Ensure required bash files exist.
    if (not os.path.isfile(localSettingsPath)):
        log("ERROR: missing files",
            "can't find {}".format(localSettingsPath))
        exit(1)

    # Source shared settings, print bash environment variables, parse meaningful values
    settings = local_shell_wrapper('bash -c \"source {} && env | grep = | grep -v :\"'.format(localSettingsPath))

    # Capture environment variables for later use.
    for line in settings.splitlines():
        (key, _, value) = line.partition("=")
        os.environ[key] = value
        #log_verbose("key:   " + key,
        #            "value: " + value)

    # Set vairables
    remoteBashPath =     os.path.join(os.environ["destination"], bashFileName)
    remoteSettingsPath = os.path.join(os.environ["destination"], settingsFileName)
    localAggregatePath = os.path.join(os.environ["HOME"], os.environ["gitAll"])

    stop_clock(timingNotification)
