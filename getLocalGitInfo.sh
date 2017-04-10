#!/bin/bash
# Copyright (c) Microsoft Corporation. All Rights Reserved.
# Licensed under the MIT license. See LICENSE file on the project webpage for details.

set -e

# Load Settings.
scriptDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $scriptDir/settings.sh

echo $gitHashFile
echo $commitHash
echo $gitUrlFile
echo $gitDetailedFile
exit 1

set -x

# Cleanup from previous run.
rm -rf "$workingDir"
mkdir -p -v "$workingDir"

# Generate list of all local git enlistments.
# This searches an entire machine's directory tree so we only do this once.
# todo4: perf optimization param that persists this file.
gitDirFilePath="$HOME/$gitDirFile"
if [ ! -f $gitDirFilePath ]; then
    # Don't exit on error. A few directories can't be searched.
    set +e
        #todo2: Pick one
        find / -name \.git -type d > $gitDirFilePath
        sudo find / -name \.git -type d > "${gitDirFilePath}.sudo${fileSuffix}"
    set -e

    # We temporarily disabled "exit on error" so let's test for success before continuing.
    if [ ! -f $gitDirFilePath ]; then
        echo "failed to create file listing local git repository paths"
        exit 1
    fi
fi

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
        printf "$withDelim" >> $workingDir/$gitDetailedFile
    done

    # newline
    echo >> $workingDir/$gitDetailedFile
}

get_branch()
{
    # Current branch is prefixed with an asterisk. Remove it.
    branchInfo=`git branch | grep '\*' | sed 's/* //g'`

    # Ensure branch information is useful.
    if [ -z "$branchInfo" ] || [[ $branchInfo == *"no branch"* ]] || [[ $branchInfo == *"detached"* ]]; then
        # Get list of branches that share the current commit and
        # remove redundant (like  "origin/HEAD -> origin/master")
        branchesWithThisCommit="`git branch --remote --contains | grep -v '>'`"

        # Fromat string.
        if [[ ! -z "$branchesWithThisCommit" ]]; then
            # Add explanation if there are more than one branches.
            multipleBranchExplanation=""
            branchCount=`echo "$branchesWithThisCommit" | wc -l`
            if (( $branchCount > "1" )); then
                # Prefix message for more than one branches.
                multipleBranchExplanation="$branchCount branches contain current commit:\n"
            else
                # Remove indentation for single branch.
                branchesWithThisCommit=`echo $branchesWithThisCommit | sed 's/  //g'`
            fi

            branchInfo="${multipleBranchExplanation}${branchesWithThisCommit}"
        fi
    fi

    echo "$branchInfo"
}

get_tag()
{
    prefix="tag:" #todo5: use, add a count, show header similar to branches
    # Get information, split into multiple lines, only keep values prefixed with 'tag:'
    tagInfo=`git log -g --decorate -1 | tr ',' '\n' | tr ')' '\n' | grep -o -i 'tag:.*'`

    #If no explicitly created tags, then look for implicit tagging information.
    if [ -z "$tagInfo" ]; then
        # Don't exit on error. There won't always be implicit tag information.
        set +e
            # Implicit tag created by a commit after a tag
            # Format: <prevTag>-<commitHash>
            autoTag=`git describe --tags`

            # Implicit tag created by a commit that happens before a tag.
            # Format: <nextTag>~<numberOfCommitsUntilNextTag>
            nextTag=`git describe --contains`

            # For old versions of git (like 1.7.9.5)
            if [ -z $nextTag ]; then
                # Uses commit hash to get label then parse tag.
                nextTag=`git rev-parse HEAD | git name-rev --stdin | grep -o 'tags/.*)' | sed 's/tags\///g' | tr ')' ' '`
            fi
        set -e

        # We temporarily disabled "exit on error" so let's test the results before using them.
        # Format string.
        if [ ! -z $autoTag ]; then
            tagInfo="tag: $autoTag \n (note: $1 is current commit's short hash)"
        fi
        if [ ! -z $autoTag ] && [ ! -z $nextTag ]; then
            # Separate with newline if both automatic tags are available.
            tagInfo="${tagInfo}\n"
        fi
        if [ ! -z $nextTag ]; then
            commitCount=`echo $nextTag | grep -o '~.*' | tr '~' ' '`
            shortNextTag=`echo $nextTag | grep -o '.*~' | tr '~' ' '`
            tagInfo="${tagInfo}tag: $nextTag \n (note:$commitCount commits after current state until tag $shortNextTag)"
        fi
    fi

    echo "$tagInfo"
}


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
    echo "$syncTime" >> $workingDir/$gitTimeFile

    # Sanitize token from URL before writing to file.
    remote=`git config --get remote.origin.url | sed 's/\/\/.*@/\/\//g'`
    echo "$remote" >> $workingDir/$gitUrlFile

    currentBranch=`get_branch`
    echo "$currentBranch" >> $workingDir/$gitBranchFile

    latestCommitHash=`git log --pretty=format:"%h" -1`
    echo "$latestCommitHash" >> $workingDir/$gitHashFile

    currentTags=`get_tag $latestCommitHash`
    echo "$currentTags" >> $workingDir/$gitTagFile

    latestCommitDate=`git log --pretty=format:"%ai" -1`
    echo "$latestCommitDate" >> $workingDir/$gitCommitDateFile

    latestCommitDesc=`git log --pretty=format:"%s" -1`
    echo "$latestCommitDesc" >> $workingDir/$gitCommitDescFile

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
done < $gitDirFilePath

#todo3: verify all line counts are equal (except for branches, tags, and final csv file. Those can each have "in-cell" newlines)

# This statement only makes sense with set -e
echo
echo "Finished with no errors!"
echo "See $workingDir/$gitDetailedFile"
echo
wc ${gitDirFilePath}* #todo2
echo
