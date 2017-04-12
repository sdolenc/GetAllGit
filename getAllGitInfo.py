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
import getpass
import datetime
import subprocess
from pssh import ParallelSSHClient

isVerbose = True    # more console messages
isDebug = True      # worse perf, but better for debugging.

# ---- # # ---- # # ---- # # ---- # # ---- # # ---- # 

def log(header, message):
    print
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

# No logging.
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

def remote_shell_wrapper(sshClientObj, command):
    log_verbose("remote bash command:", command)

    output = sshClientObj.run_command(command, stop_on_errors=False, user=getpass.getuser())

    # If debugging then wait for all parellel operations to complete
    debug_mode(sshClientObj, output)
    return output

def copy_to_remote(sshClientObj, localFile, remoteFile):
    log_verbose("copy:      " + localFile,
                "to remote: " + remoteFile)

    sshClientObj.copy_file(localFile, remoteFile)

    # If debugging then wait for all parellel operations to complete
    debug_mode(sshClientObj)

def copy_from_remote(sshClientObj, remoteFile, destinationFilePrefix):
    log_verbose("copy from remote: " + remoteFile,
                "to local:         {}_<host>".format(destinationFilePrefix))

    sshClientObj.copy_remote_file(remoteFile, destinationFilePrefix)

    # If debugging then wait for all parellel operations to complete
    debug_mode(sshClientObj)

# ---- # # ---- # # ---- # # ---- # # ---- # # ---- # 

startTimes = dict() # key=uniqueStr, value=start.

def start_clock(message):
    log("running \"{}\" operation...".format(message), "")

    startTimes[message] = datetime.datetime.now()

def stop_clock(message):
    totalSeconds = datetime.datetime.now() - startTimes.pop(message)

    log("operation: \"{}\" complete".format(message),
        "took:      \"{}\" seconds".format(totalSeconds))

# ---- # # ---- # # ---- # # ---- # # ---- # # ---- # 

# Finds values between 0 and 999.
threeNumbersRegex = "[0-9]{1,3}"

# Grabs first 3 octets (24 bits) of the current machine's ipv4 address.
# Example result: 10.0.0.
# Note: trailing period is included
def get_local_ipv4_prefix():
    return local_shell_wrapper('hostname -I | grep -oE \"({}\.){}\"'.format(threeNumbersRegex, "{3}"))
    #Consider: supporting ipv6
    #Consider: returning list if machine has multiple ipv4 addresses.

# Looks for nearby hosts in /24 ipv4 neighborhood (the
# 255 addresses contained in the last ip octet).
def get_host_list(ipPrefix):
    # Get string of hosts separated by newlines
    range = "1-255"
    strHosts = local_shell_wrapper('nmap -sP {}{} | grep -oE \"{}({})\"'.format(ipPrefix, range, ipPrefix, threeNumbersRegex))

    # Make list object.
    return strHosts.splitlines()

# ---- # # ---- # # ---- # # ---- # # ---- # # ---- # 

# Blocks execution until all parallel operations complete (worse perf).
def join_wrapper(sshClientObj, output=None):
    sshClientObj.pool.join(raise_error=True)
    if isVerbose and output:
        for host in sshClientObj.hosts:
            for line in output[host].stderr:
                log_verbose(host + " error: ", line)
            #fyi, regular output in output[host].stdout:

def debug_mode(sshClientObj, output=None):
    if isDebug:
        join_wrapper(sshClientObj, output)

# ---- # # ---- # # ---- # # ---- # # ---- # # ---- # 

globalClock="all tasks"

start_clock(globalClock)

# ---- # # ---- # # ---- # # ---- # # ---- # # ---- # 

timingNotification="get shared settings"

start_clock(timingNotification)

# Directory of this python file.
scriptDir = os.path.dirname(os.path.realpath(__file__))

# Ensure required bash files are also in this directory.
bashFileName =      "getLocalGitInfo.sh"
settingsFileName =  "settings.sh"
localBashPath =     os.path.join(scriptDir, bashFileName)
localSettingsPath = os.path.join(scriptDir, settingsFileName)
if ((not os.path.isfile(localBashPath)) or (not os.path.isfile(localSettingsPath))):
    log("ERROR: missing file(s)",
        "can't find {} and/or {}".format(localBashPath, localSettingsPath))
    exit(1)

# Source shared settings.
settings = local_shell_wrapper('bash -c \"source {} && env | grep = | grep -v :\"'.format(localSettingsPath))
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

# ---- # # ---- # # ---- # # ---- # # ---- # # ---- # 

timingNotification="finding hosts"

start_clock(timingNotification)

ipPrefix = get_local_ipv4_prefix()

hosts = get_host_list(ipPrefix)

# Create parallel SSH
client = ParallelSSHClient(hosts)

stop_clock(timingNotification)

# ---- # # ---- # # ---- # # ---- # # ---- # # ---- # 

timingNotification="copy/execute script on machines"

start_clock(timingNotification)

# Cleanup from previous run by removing existing script file.
remote_shell_wrapper(client, "rm -f " + remoteBashPath)
remote_shell_wrapper(client, "rm -f " + remoteSettingsPath)

# Copy bash file to all machines.
copy_to_remote(client, localBashPath, remoteBashPath)
copy_to_remote(client, localSettingsPath, remoteSettingsPath)

# Run script.
output = remote_shell_wrapper(client, "bash " + remoteBashPath)

join_wrapper(client, output)
stop_clock(timingNotification)

# ---- # # ---- # # ---- # # ---- # # ---- # # ---- # 

timingNotification="aggregate results"

start_clock(timingNotification)

# Cleanup from previous run
local_shell_wrapper("rm -rf " + localAggregatePath)

# Copy output files to central location. This creates directory.
copy_from_remote(client,
                 os.environ["gitDetailedFile"],
                 os.path.join(localAggregatePath, os.environ["gitAll"]))
copy_from_remote(client,
                 os.environ["gitDirFile"],
                 os.path.join(localAggregatePath, os.environ["dir"]))

join_wrapper(client)

log_verbose("appending extensions and creating merged csv file...", "")

mergedCsvPath = os.path.join(localAggregatePath, os.environ["gitAll"] + os.environ["outputSuffix"])
mergedCsv = open(mergedCsvPath, "wb")
mergedHasHeader = False

for fileName in os.listdir(localAggregatePath):
    if "_" in fileName:
        if os.environ["gitAll"] in fileName:
            # Merge CSVs
            sourceCsv = os.path.join(localAggregatePath, fileName)
            readFrom = open(sourceCsv)
            header = next(readFrom)
            if not mergedHasHeader:
                mergedCsv.write(header)
                mergedHasHeader = True
            for line in readFrom:
                mergedCsv.write(line)
            readFrom.close()

            # Add csv extension.
            os.rename(sourceCsv,
                      os.path.join(localAggregatePath, fileName + os.environ["outputSuffix"]))
        elif os.environ["dir"] in fileName:
            # Add text extension.
            os.rename(os.path.join(localAggregatePath, fileName),
                      os.path.join(localAggregatePath, fileName + os.environ["fileSuffix"]))

mergedCsv.close()
stop_clock(timingNotification)

# ---- # # ---- # # ---- # # ---- # # ---- # # ---- # 

stop_clock(globalClock)