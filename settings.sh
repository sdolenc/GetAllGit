#!/bin/bash
# Copyright (c) Microsoft Corporation. All Rights Reserved.
# Licensed under the MIT license. See LICENSE file on the project webpage for details.

fileSuffix=".txt"
outputSuffix=".csv"
delim=","

# All output pathnames will have this variable.
outputPrefix="gitInfo"

get_working_dir()
{
    basePath="$HOME"
    if [ -d "/tmp" ]; then
        basePath="/tmp"
    elif [ -d "/var/tmp" ]; then
        basePath="/var/tmp"
    fi

    echo "${basePath}/${outputPrefix}"
}

# Directory to write files to.
workingDir=`get_working_dir`

get_full_file_path()
{
    echo "$workingDir/${1}${2}"
}

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
    