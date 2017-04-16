#!/usr/bin/python
# Copyright (c) Microsoft Corporation. All Rights Reserved.
# Licensed under the MIT license. See LICENSE file on the project webpage for details.

import subprocess

# more console messages
isVerbose = True

def log(header, message):
    print(header)
    print(message)
    print

# Less important messages.
def log_verbose(header, message):
    if isVerbose:
        log(indent(header), indent(message))

# Indent each line of a string
def indent(anyString):
    return local_shell_quiet("printf \'{}\' | sed -e 's/^/  /'".format(anyString))

# No logging. Helper function.
def local_shell_quiet(command):
    p = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
    out, err = p.communicate()
    return out

def local_shell_wrapper(command):
    log_verbose("local bash command:", command)

    # Trim leading/trailing whitespace
    out = local_shell_quiet(command).strip()

    log_verbose("local bash results:", out)

    return out
