#!/usr/bin/python
# Copyright (c) Microsoft Corporation. All Rights Reserved.
# Licensed under the MIT license. See LICENSE file on the project webpage for details.

#PRE-REQUISITES:
#   - nmap already installed #todo:later maybe install nmap within this script?
#   - pip install -r requirements.txt
#   - all machines in the same 24bit ip address neighborhood have
#       a) ssh installed
#       b) the ssh credentials enabled for connections (with ssh-add, etc)
#           in other words, the machine running this script should be able
#           to "ssh <ipOtherMachine>"
#       c) have same username as current logged in getpass.getuser() #todo:needed?

#todo:later "Consider" comments below are low-priority feature ideas.

import os
import pprint
import getpass
import datetime
import subprocess
from pssh import ParallelSSHClient

bashFileName = "getLocalGitInfo.sh" # todo1

#todo:later move to script paramters
isVerbose = True    # more console messages
#todo:
isDebug = True      # worse perf, but better for debugging.

startTimes = dict() # key=uniqueStr, value=start.

# Finds values between 0 and 999.
threeNumbersRegex = "[0-9]{1,3}"
scriptDir = os.path.dirname(os.path.realpath(__file__))
destinationDir = "/tmp"

# ---- # # ---- # # ---- # # ---- # # ---- # # ---- # 

# Less important messages.
def verbose(header, message):
    if isVerbose:
        log(header, message)

# Always log
def log(header, message):
    print
    print(header)
    print(message)
    print

def start_clock(message):
    verbose("running \"{}\" operation".format(message), "...")
    startTimes[message] = datetime.datetime.now()

def stop_clock(message):
    totalSeconds = datetime.datetime.now() - startTimes.pop(message)
    log("operation \"{}\" took".format(message),
        "{} total seconds".format(totalSeconds))

# Grabs first 3 octets (24 bits) of the current machine's ipv4 address.
# Example result: 10.0.0.
# Note: trailing period is included
def get_local_ipv4_prefix():
    return local_shell_wrapper("hostname -I | grep -oE '({}\.){}'".format(threeNumbersRegex, "{3}"))
    #Consider: supporting ipv6
    #Consider: returning list if machine has multiple ipv4 addresses.

# Looks for nearby hosts in /24 ipv4 neighborhood (the
# 255 addresses contained in the last ip octet).
def get_host_list(ipPrefix):
    # Get string of hosts separated by newlines
    range = "1-255"
    strHosts = local_shell_wrapper("nmap -sP {}{} | grep -oE '{}({})'".format(ipPrefix, range, ipPrefix, threeNumbersRegex))

    # Make list object.
    return strHosts.splitlines()

def local_shell_wrapper(command):
    verbose("local bash command:", command)

    p = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
    out, err = p.communicate()

    verbose("local bash results:", out)

    #todo:later error handling

    # trim leading/trailing whitespace
    return out.strip()

def remote_shell_wrapper(sshClientObj, command):
    # todo:later error handling
    output = sshClientObj.run_command(command, stop_on_errors=False, user=getpass.getuser())
    debug_mode(sshClientObj)
    return output

#todo: should take output and write to console if verbose.
def debug_mode(sshClientObj):
    if isDebug:
        join_wrapper(sshClientObj)

# Blocks execution until all parallel operations complete (worse perf).
def join_wrapper(sshClientObj):
    sshClientObj.pool.join(raise_error=True)

# ---- # # ---- # # ---- # # ---- # # ---- # # ---- # 

timingNotification="finding hosts"

start_clock(timingNotification)

ipPrefix = get_local_ipv4_prefix()

hosts = get_host_list(ipPrefix)

stop_clock(timingNotification)

# ---- # # ---- # # ---- # # ---- # # ---- # # ---- # 

timingNotification="copy/execute script on machines then aggregate results"

start_clock(timingNotification)

# Create parallel SSH
client = ParallelSSHClient(hosts)

#todo1
remoteScriptPath = os.path.join(destinationDir, bashFileName)

#todo: test everything below this.
# Remove any existing script file
remote_shell_wrapper(client, "rm -f " + remoteScriptPath)

# Copy bash file to all machiens.
client.copy_file(os.path.join(scriptDir, bashFileName), remoteScriptPath)
debug_mode(client)

# Run script.
output = remote_shell_wrapper(client, "bash " + remoteScriptPath)

# Copy output files to central location. #todo1
try:
    client.copy_remote_file("/tmp/gitInfo/AllGitDetails_.csv", "/home/lexoxaadmin/all/AllGitDetails_.csv")
except:
    pass
try:
    client.copy_remote_file("/home/lexoxaadmin/gitInfo_directory.txt", "/home/lexoxaadmin/all/gitInfo_directory.txt")
except:
    pass
try:
    client.copy_remote_file("/home/lexoxaadmin/gitInfo_directory.txt.sudo.txt", "/home/lexoxaadmin/all/gitInfo_directory.txt.sudo.txt")
except:
    pass

join_wrapper(client)

#todo: collect all outputs and move to move to debug function
#pprint.pprint(output)
#def debugger():
#for host in output:
def debugger2(host):
    print(host)
    print(output[host].cmd)
    for line in output[host].stderr:
        print(line)
    for line in output[host].stdout:
        print(line)
#debugger2("10.0.0.4")

stop_clock(timingNotification)

#todo: merge and remove all, but one header
