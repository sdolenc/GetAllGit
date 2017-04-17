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
    os.environ["scriptDir"] = os.path.dirname(os.path.realpath(__file__))

    bashFileName =      "getLocalGitInfo.sh"
    settingsFileName =  "settings.sh"
    os.environ["localBashPath"] =     os.path.join(os.environ["scriptDir"], bashFileName)
    os.environ["localSettingsPath"] = os.path.join(os.environ["scriptDir"], settingsFileName)

    # Ensure required bash files exist.
    if (not os.path.isfile(os.environ["localSettingsPath"])):
        log("ERROR: missing files",
            "can't find {}".format(os.environ["localSettingsPath"]))
        exit(1)

    # Source shared settings, print bash environment variables, parse meaningful values
    settings = local_shell_wrapper('bash -c \"source {} && env | grep = | grep -v :\"'.format(os.environ["localSettingsPath"]))

    # Capture environment variables for later use.
    for line in settings.splitlines():
        (key, _, value) = line.partition("=")
        os.environ[key] = value
        #log_verbose("key:   " + key,
        #            "value: " + value)

    # Set vairables
    os.environ["remoteBashPath"] =     os.path.join(os.environ["destination"], bashFileName)
    os.environ["remoteSettingsPath"] = os.path.join(os.environ["destination"], settingsFileName)

    stop_clock(timingNotification)
