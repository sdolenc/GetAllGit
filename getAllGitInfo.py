#!/usr/bin/python
# Copyright (c) Microsoft Corporation. All Rights Reserved.
# Licensed under the MIT license. See LICENSE file on the project webpage for details.


#todo: is this the best way of invoking bash in python?
# Grabs first ipv4 occurence.
# Consider: expanding for ipv6 and more than one address
s = subprocess.Popen(["get ip prefix hostname -I | grep -oE '([0-9]{1,3}\.){3}'"], shell=True, stdout=subprocess.PIPE).stdout
ipAddress = s.read()

#todo: consider switching to python library with similar nmap functionality.
#No harm in attempting to install nmap even if it's already available. It's a fast no-op.
#todo: sudo apt-get install nmap
s = subprocess.Popen(["nmap -sP ${prefix}1-255 | grep -oE '${prefix}([0-9]{1,3})'"], shell=True, stdout=subprocess.PIPE).stdout
ipAddresses = s.read().splitlines()

#todo: https://github.com/ParallelSSH/parallel-ssh

#todo:bigTodo
'''
verify the jb can delegate to itself

copy_file script (instead of wget or curl from github)
 support overwrite? (so latest changes are picked up)
execute script
copy_remote_file (instead of scp->jumpbox)
 2x git directory files,merged detailed

The client's join function can be used to block and wait for all parallel commands to finish:
client.join(output)

output.values()[i].exit_code
if !0 then write look at output

merge and remove all, but one header
'''
