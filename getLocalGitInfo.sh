#!/bin/bash
# Copyright (c) Microsoft Corporation. All Rights Reserved.
# Licensed under the MIT license. See LICENSE file on the project webpage for details.

set -e

# Load Settings.
scriptDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $scriptDir/settings.sh

set -x # optional

initialize()
{
    # Cleanup from previous run.
    rm -rfv "$workingDir"
    mkdir -p -v "$workingDir"

    # Generate list of all local git enlistments.
    # This searches an machine's entire directory tree.
    # todo: (perf optimization) param that persists this file for next run.
    if [ ! -f $gitDirFile ]; then
        # Don't exit on error. A few directories can't be searched.
        set +e
            echo "This operation takes a few seconds..."
            find / -name \.git -type d 2> /dev/null 1> $gitDirFile
        set -e

        # We temporarily disabled "exit on error" so let's test for success before continuing.
        if [ ! -f $gitDirFile ]; then
            echo "failed to create file listing local git repository paths"
            exit 1
        fi
    fi
}

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
        printf "$withDelim" >> $gitDetailedFile
    done

    # newline
    echo >> $gitDetailedFile
}

format_list()
{
    list="$1"
    message="$2"

    # Format string.
    if [[ ! -z "$list" ]]; then
        # Add explanation if there are more than one branches.
        count=`echo -e "$list" | wc -l`
        if (( $count > "1" )); then
            # Prefix message with list size.
            message="$count $message"
            list="${message}:\n${list}"
        else
            # Remove indentation for single branch.
            list=`echo $list | tr -d ' '`
        fi
    fi

    echo "$list"
}

get_branch()
{
    prefix='* '

    # Current branch is prefixed with an asterisk. Remove it.
    branchInfo=`git branch | grep "$prefix" | sed "s/$prefix//g"`

    # Ensure branch information is useful.
    if [ -z "$branchInfo" ] || [[ $branchInfo == *"no branch"* ]] || [[ $branchInfo == *"detached"* ]]; then
        # Get list of branches that share the current commit, remove redundant (like  "origin/HEAD -> origin/master")
        branchInfo="`git branch --remote --contains | grep -v '>' | sed 's/origin\///g'`"

        branchInfo=`format_list "$branchInfo" "branches contain current commit"`
    fi

    echo "$branchInfo"
}

get_tag()
{
    prefix="tag: "

    # First see if there are named tag(s) for the current commit.
    # Allow errors. This syntax isn't supported on old versions of git (like 1.7.9.5)
    set +e
    tagInfo=`git tag -l --points-at HEAD 2> /dev/null | sed -e 's/^/  /'`
    set -e

    # For old versions of git (like 1.7.9.5)
    if [ -z $tagInfo ]; then
        # Get information, split into multiple lines, only keep values prefixed with 'tag:', remove prefix
        tagInfo=`git log -g --decorate -1 | tr ',' '\n' | tr ')' '\n' | grep -o -i "${prefix}.*" | sed "s/${prefix}/  /g"`
    fi

    # If no explicitly created tags, then look for implicit tagging information.
    if [ -z "$tagInfo" ]; then
        # Don't exit on error. There won't always be implicit tag information.
        set +e
            # Implicit tag created by a commit after a tag
            # Format: <prevTag>-<commitHash>
            autoTag=`git describe --tags 2> /dev/null`

            # Implicit tag created by a commit that happens before a tag.
            # Format: <nextTag>~<numberOfCommitsUntilNextTag>
            nextTag=`git describe --contains 2> /dev/null`

            # For old versions of git (like 1.7.9.5)
            if [ -z $nextTag ]; then
                # Uses commit hash to get label then parse tag.
                nextTag=`git rev-parse HEAD | git name-rev --stdin --tags | grep -o 'tags/.*)' | sed 's/tags\///g' | tr ')' ' '`
            fi
        set -e

        # We temporarily disabled "exit on error" so let's test the results before using them.
        if [ ! -z $autoTag ]; then
            tagInfo="  $autoTag"
        fi
        if [ ! -z $autoTag ] && [ ! -z $nextTag ]; then
            # Separate with newline if both automatic tags are available.
            tagInfo="${tagInfo}\n"
        fi
        if [ ! -z $nextTag ]; then
            tagInfo="${tagInfo}  $nextTag"
        fi
    fi

    tagInfo=`format_list "$tagInfo" "tags point to current commit"`

    echo "$tagInfo"
}

initialize

# Write CSV header.
# The first four columns are:
#   - somewhat static for a given machine so they're set outside of the loop.
#   - more helpful when results from more than one machine are merged
# The remaining columns are:
#   - also represented in corresponding files in $workingDir .
write_separated_values  "machine" \
                        "ipAdresses" \
                        "osVer" \
                        "gitVer" \
                        "$dir" \
                        "$url" \
                        "$branch" \
                        "$tag" \
                        "$commitDate" \
                        "$commitDesc" \
                        "$commitHash" \
                        "$time (accuracy not guarenteed)"

# Put all machine ip addresses on their own line.
ip=`hostname -I | tr ' ' '\n'`
osVer=`lsb_release -rs`
gitVer=`git --version | grep -o '[0-9].*'`

# Iterate over list of local git enlistments.
while read entry; do
    pushd ${entry}/..

    # FETCH_HEAD file's modified timestamp is changed everytime git pulls from remote server.
    # We do this first in case one of the operation below happen to modify the timestamp.
    syncTime=""
    if [ -f .git/FETCH_HEAD ]; then
        syncTime=`stat -c %y .git/FETCH_HEAD`
    fi
    echo "$syncTime" >> $gitTimeFile

    # Sanitize token from URL before writing to file.
    remote=`git config --get remote.origin.url | sed 's/\/\/.*@/\/\//g'`
    echo "$remote" >> $gitUrlFile

    # Get latest upstream information. This won't sync or merge any code.
    # - before retriving branch and tag information.
    # - after recording syncTime (as this updateds FETCH_HEAD's timestamp)
    # We allow for failure in case network connectivity or trouble elevating.
    set +e
    sudo git fetch
    set -e

    currentBranch=`get_branch`
    echo "$currentBranch" >> $gitBranchFile

    currentTags=`get_tag`
    echo "$currentTags" >> $gitTagFile

    latestCommitDate=`git log --pretty=format:"%ai" -1`
    echo "$latestCommitDate" >> $gitCommitDateFile

    latestCommitDesc=`git log --pretty=format:"%s" -1`
    echo "$latestCommitDesc" >> $gitCommitDescFile

    # Short hash
    latestCommitHash=`git log --pretty=format:"%h" -1`
    echo "$latestCommitHash" >> $gitHashFile

    # Write CSV values.
    write_separated_values  "$HOSTNAME" \
                            "$ip" \
                            "$osVer" \
                            "$gitVer" \
                            "`pwd`" \
                            "$remote" \
                            "$currentBranch" \
                            "$currentTags" \
                            "$latestCommitDate" \
                            "$latestCommitDesc" \
                            "$latestCommitHash" \
                            "${syncTime}"

    popd
done < $gitDirFile

# This statement only makes sense with set -e
echo
echo "Finished with no errors!"
echo "See $gitDetailedFile"
echo
