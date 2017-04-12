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

#todo: move to script paramters
isVerbose = False   # more console messages
isDebug = False     # worse perf, but better for debugging.

# ---- # # ---- # # ---- # # ---- # # ---- # # ---- # 

def log(header, message):
    print
    print(header)
    print(message)
    print

# Less important messages.
def verbose(header, message):
    if isVerbose:
        log(header, message)

def local_shell_wrapper(command):
    verbose("local bash command:", command)

    p = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
    out, err = p.communicate()

    verbose("local bash results:", out)

    # trim leading/trailing whitespace
    return out.strip()

def remote_shell_wrapper(sshClientObj, command):
    output = sshClientObj.run_command(command, stop_on_errors=False, user=getpass.getuser())
    # If debugging then wait for all parellel operations to complete
    debug_mode(sshClientObj, output)
    return output

def copy_to_remote(sshClientObj, localFile, remoteFile):
    sshClientObj.copy_file(localFile, remoteFile)
    # If debugging then wait for all parellel operations to complete
    debug_mode(sshClientObj)

# ---- # # ---- # # ---- # # ---- # # ---- # # ---- # 

startTimes = dict() # key=uniqueStr, value=start.

def start_clock(message):
    verbose("running \"{}\" operation".format(message), "...")
    startTimes[message] = datetime.datetime.now()

def stop_clock(message):
    totalSeconds = datetime.datetime.now() - startTimes.pop(message)
    log("operation: {}".format(message),
        "took:      {} total seconds".format(totalSeconds))

# ---- # # ---- # # ---- # # ---- # # ---- # # ---- # 

# Finds values between 0 and 999.
threeNumbersRegex = "[0-9]{1,3}"

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

# ---- # # ---- # # ---- # # ---- # # ---- # # ---- # 

# Blocks execution until all parallel operations complete (worse perf).
def join_wrapper(sshClientObj, output=None):
    sshClientObj.pool.join(raise_error=True)
    if isVerbose and output:
        for host in sshClientObj.hosts:
            verbose("command on",
                    "host " + str(host))
            #verbose("", "regular output:")
            #for line in output[host].stdout:
            #    print(line)
            for line in output[host].stderr:
                verbose("error:", line)

def debug_mode(sshClientObj, output=None):
    if isDebug:
        join_wrapper(sshClientObj, output)

# ---- # # ---- # # ---- # # ---- # # ---- # # ---- # 

timingNotification="parsing shared settings"

start_clock(timingNotification)

# Directory of this python file.
scriptDir = os.path.dirname(os.path.realpath(__file__))

# Ensure required bash files are also in this directory.
bashFileName = "getLocalGitInfo.sh"
settingsFileName = "settings.sh"
localBashPath =     os.path.join(scriptDir, bashFileName)
localSettingsPath = os.path.join(scriptDir, settingsFileName)
if ((not os.path.isfile(localBashPath)) or (not os.path.isfile(localSettingsPath))):
    log("ERROR: missing file(s)", "can't find {} and/or {}".format(localBashPath, localSettingsPath))
    exit(1)

# Source shared settings.
settings = local_shell_wrapper("bash -c \"source {} && env | grep '=' | grep -v ';\|:'\"".format(localSettingsPath))
for line in settings.splitlines():
    (key, _, value) = line.partition("=")
    os.environ[key] = value
    verbose("key   " + key, "value " + value)

# Set vairables
remoteBashPath =     os.path.join(os.environ["destination"], bashFileName)
remoteSettingsPath = os.path.join(os.environ["destination"], settingsFileName)

stop_clock(timingNotification)

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

# Cleanup from previous run by removing existing script file.
remote_shell_wrapper(client, "rm -f " + remoteBashPath)
remote_shell_wrapper(client, "rm -f " + remoteSettingsPath)

# Wait for removals to complete.
join_wrapper(client)

# Copy bash file to all machines.
copy_to_remote(client, localBashPath, remoteBashPath)
copy_to_remote(client, localSettingsPath, remoteSettingsPath)

# Run script.
output = remote_shell_wrapper(client, "bash " + remoteBashPath)

join_wrapper(client, output)
stop_clock(timingNotification)
exit(3) #todo:

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


#todo: merge and remove all, but one header
