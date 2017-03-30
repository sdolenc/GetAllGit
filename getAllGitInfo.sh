#!/bin/bash
# Copyright (c) Microsoft Corporation. All Rights Reserved.
# Licensed under the MIT license. See LICENSE file on the project webpage for details.

fileSuffix=".txt"
outputSuffix=".csv"
 # Shouldn't be ' ' (space) character.
delim=","

# Generated first and becomes primary "input"
    dir="directory"
    gitDirFile="${dir}${fileSuffix}"
# Partial output (csv table columns)
    url="remoteUrl"
    gitUrlFile="${url}${fileSuffix}"
    branch="currentBranch"
    gitBranchFile="${branch}${fileSuffix}"
    tag="tags"
    gitTagFile="${tag}${fileSuffix}"
    time="syncTime"
    gitTimeFile="${time}${fileSuffix}"
    commitDate="currentCommitDate"
    gitCommitDateFile="${commitDate}${fileSuffix}"
    commitDesc="currentCommitDescription"
    gitCommitDescFile="${commitDesc}${fileSuffix}"
    commitHash="currentCommitHash"
    gitHashFile="${commitHash}${fileSuffix}"
# Total output.
    gitDetailedFile="AllGitDetails_${HOSTNAME}${outputSuffix}"

set -xe

# Directory to write files to.
basePath="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ -d "/tmp" ]; then
    basePath="/tmp"
elif [ -d "/var/tmp" ]; then
    basePath="/var/tmp"
fi

# Generate list of all local git enlistments.
# This searches an entire machine's directory tree so we only do this once.
gitDirFilePath="$basePath/$gitDirFile"
if [ ! -f $gitDirFilePath ]; then
    # Don't exit on error. A few directories can't be searched
    set +e
    # Pick one
    find / -name \.git -type d > $gitDirFilePath
    sudo find / -name \.git -type d > "${gitDirFilePath}2.txt"
    set -e
fi

workingDir="${basePath}/gitInfo_${HOSTNAME}"
gitDetailedFilePath="$workingDir/$gitDetailedFile"

# Cleanup from previous run. Doesn't remove $gitDirFile
rm -rf "$workingDir"
mkdir -p -v "$workingDir"

append_delim()
{
    # Remove any existing delimeters.
    clean=`echo "${1}" | tr $delim ' '`

    # Wrap value in quotes and append one trailing delimeter.
    echo "\"${clean}\"${delim}"
}

write_separated_values()
{
    for val in "$@"; do
        withDelim=`append_delim "$val"`
        printf "$withDelim" >> $gitDetailedFilePath
    done

    # newline
    echo >> $gitDetailedFilePath
}

get_branch()
{
    # Current branch is prefixed with an asterisk. Remove it.
    branchInfo=`git branch | grep '\*' | sed 's/* //g'`

    # Ensure branch information is useful.
    if [ -z "$branchInfo" ] || [[ $branchInfo == *"no branch"* ]] || [[ $branchInfo == *"detached"* ]]; then
        # Get list of branches that share the current commit (and remove redundant "origin/HEAD -> origin/master")
        branchesWithThisCommit="`git branch --remote --contains | grep -v '>'`"

        # Fromat string.
        if [[ ! -z "$branchesWithThisCommit" ]]; then
            # Add explanation if there are more than one branches.
            multipleBranchExplanation=""
            branchCount=`echo "$branchesWithThisCommit" | wc -l`
            if (( $branchCount > "1" )); then
                multipleBranchExplanation="$branchCount branches contain current commit:\n"
            fi

            branchInfo="${multipleBranchExplanation}${branchesWithThisCommit}"
        fi
    fi

    echo "$branchInfo"
}

get_tag()
{
    # Get information, split into multiple lines, only keep values prefixed with 'tag:'
    tagInfo=`git log -g --decorate -1 | tr ',' '\n' | tr ')' '\n' | grep -o -i 'tag:.*'`

    #If no explicitly created tags, then look for implicit tagging information.
    if [ -z "$tagInfo" ]; then
        # Don't exit on error. There won't always be implicit tag information.
        set +e
        # implicit tag created by commit
        autoTag=`git describe --tags`
        # next tag and ~ number of commits until we reach it.
        nextTag=`git describe --contains`

        # For old versions of git (like 1.7.9.5)
        if [ -z $nextTag ]; then
            # Uses commit hash to get label then parse tag.
            nextTag=`git rev-parse HEAD | git name-rev --stdin | grep -o 'tags/.*^)' | sed 's/tags\///g' | tr ')' ' '`
        fi
        set -e

        # Format string.
        if [ ! -z $autoTag ]; then
            tagInfo="tag: $autoTag \n (note: $1 is current commit's short hash) \n"
        fi
        if [ ! -z $nextTag ]; then
            commitCount=`echo $nextTag | grep -o '~.*' | tr '~' ' '`
            shortNextTag=`echo $nextTag | grep -o '.*~' | tr '~' ' '`
            tagInfo="${tagInfo}tag: $nextTag \n (note:$commitCount commits after current state until tag $shortNextTag)"
        fi
    fi

    echo "$tagInfo"
}


# Write CSV header. These each have corresponding files in $workingDir
write_separated_values  "machine" \
                        "ipAdresses" \
                        "$dir" \
                        "$url" \
                        "$branch" \
                        "$tag" \
                        "$time" \
                        "$commitDate" \
                        "$commitDesc" \
                        "$commitHash"

# Put all machine ip addresses on their own line.
ip=`hostname -I | tr ' ' '\n'`

# Iterate over list of local git enlistments.
while read entry; do
    pushd ${entry}/..

    # Sanitize token from URL before writing to file.
    remote=`git config --get remote.origin.url | sed 's/\/\/.*@/\/\//g'`
    echo "$remote" >> $workingDir/$gitUrlFile

    currentBranch=`get_branch`
    echo "$currentBranch" >> $workingDir/$gitBranchFile

    latestCommitHash=`git log --pretty=format:"%h" -1`
    echo "$latestCommitHash" >> $workingDir/$gitHashFile

    currentTags=`get_tag $latestCommitHash`
    echo "$currentTags" >> $workingDir/$gitTagFile

    # FETCH_HEAD file's modified timestamp is changed everytime git pulls from remote server.
    syncTime=""
    if [ -f .git/FETCH_HEAD ]; then
        syncTime=`stat -c %y .git/FETCH_HEAD`
    fi
    echo "$syncTime" >> $workingDir/$gitTimeFile

    latestCommitDate=`git log --pretty=format:"%ad" -1`
    echo "$latestCommitDate" >> $workingDir/$gitCommitDateFile

    latestCommitDesc=`git log --pretty=format:"%s" -1`
    echo "$latestCommitDesc" >> $workingDir/$gitCommitDescFile

    # Write CSV values.
    write_separated_values  "$HOSTNAME" \
                            "$ip" \
                            "`pwd`" \
                            "$remote" \
                            "$currentBranch" \
                            "$currentTags" \
                            "${syncTime}" \
                            "$latestCommitDate" \
                            "$latestCommitDesc" \
                            "$latestCommitHash"

    popd
done < $gitDirFilePath

#todo: verify all line counts are equal (except for git tags final csv file because those can each have "in-cell" newlines)

# This statement only makes sense with set -e
echo
echo "Finished with no errors!"
echo "See $gitDetailedFilePath"
echo

#todo: make wrapper file for parallel execution
#   input: list of scp and ssh hosts/arguments OR sibling nodes.
#   output: merged csv document -> error line of 3 fails
