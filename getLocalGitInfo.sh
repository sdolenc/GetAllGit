#!/bin/bash
# Copyright (c) Microsoft Corporation. All Rights Reserved.
# Licensed under the MIT license. See LICENSE file on the project webpage for details.

fileSuffix=".txt"
outputSuffix=".csv"
 # Shouldn't be ' ' (space) character.
delim=","

# Generated first and becomes primary "input"
    dir="directory"
    gitDirFile="gitInfo_${dir}_${HOSTNAME}${fileSuffix}"
# Partial output (csv table columns)
    url="remoteUrl"
    gitUrlFile="${url}${fileSuffix}"
    branch="currentBranch"
    gitBranchFile="${branch}${fileSuffix}"
    tag="currentTags"
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
# todo4: optional param that forces the creation of a new "git directory list" file.
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
#   - more helpful when results from more than one machine are merged. see #todo4
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
                        "$time" \
                        "$commitDate" \
                        "$commitDesc" \
                        "$commitHash"

# Put all machine ip addresses on their own line.
ip=`hostname -I | tr ' ' '\n'`
osVer=`lsb_release -rs`
gitVer=`git --version | grep -o '[0-9].*'`

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
                            "${syncTime}" \
                            "$latestCommitDate" \
                            "$latestCommitDesc" \
                            "$latestCommitHash"

    popd
done < $gitDirFilePath

#todo3: verify all line counts are equal (except for branches, tags, and final csv file. Those can each have "in-cell" newlines)

# This statement only makes sense with set -e
echo
echo "Finished with no errors!"
echo "See $gitDetailedFilePath"
echo
wc ${gitDirFilePath}* #todo2
echo

#todo1: make wrapper file for parallel execution
#   input: list of scp and ssh hosts/arguments OR sibling nodes.
#   output: merged csv document -> error line of 3 fails
