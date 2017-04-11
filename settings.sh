#!/bin/bash
# Copyright (c) Microsoft Corporation. All Rights Reserved.
# Licensed under the MIT license. See LICENSE file on the project webpage for details.

get_dir()
{
    basePath="$HOME"
    if [ -d "/tmp" ]; then
        basePath="/tmp"
    elif [ -d "/var/tmp" ]; then
        basePath="/var/tmp"
    fi

    echo "${basePath}"
}

get_full_file_path()
{
    echo "$workingDir/${1}${2}"
}

set -a

fileSuffix=".txt"
outputSuffix=".csv"
delim=","

# All output pathnames will have this variable.
outputPrefix="gitInfo"

# Directory to write files to.
destination=`get_dir`
workingDir=$destination/${outputPrefix}

# Generated first and becomes primary "input"
    dir="directory"
    gitDirFile=`        get_full_file_path "${outputPrefix}_${dir}" "${fileSuffix}"`
# Partial output (csv table columns)
    url="remoteUrl"
    gitUrlFile=`        get_full_file_path "${url}"                 "${fileSuffix}"`
    branch="currentBranch"
    gitBranchFile=`     get_full_file_path "${branch}"              "${fileSuffix}"`
    tag="currentTags"
    gitTagFile=`        get_full_file_path "${tag}"                 "${fileSuffix}"`
    time="syncTime"
    gitTimeFile=`       get_full_file_path "${time}"                "${fileSuffix}"`
    commitDate="currentCommitDate"
    gitCommitDateFile=` get_full_file_path "${commitDate}"          "${fileSuffix}"`
    commitDesc="currentCommitDescription"
    gitCommitDescFile=` get_full_file_path "${commitDesc}"          "${fileSuffix}"`
    commitHash="currentCommitHash"
    gitHashFile=`       get_full_file_path "${commitHash}"          "${fileSuffix}"`
# Total output.
    gitDetailedFile=`   get_full_file_path "${outputPrefix}_all"    "${outputSuffix}"`
    
set +a
