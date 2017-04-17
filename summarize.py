#!/usr/bin/python
# Copyright (c) Microsoft Corporation. All Rights Reserved.
# Licensed under the MIT license. See LICENSE file on the project webpage for details.

import os
import sys
import csv
import json
from helpers.sourceSettings import source_settings

# Expects directory as an argument.
if (len(sys.argv) != 2):
    print("Path Expected")
    exit(3)
csvFilePath = "/home/localstepdo/Desktop/shared/stampExample2.csv" # sys.argv[1] #todo:

if (not os.path.isfile(csvFilePath)):
    print("Path {} is not a file".format(csvFilePath))
    exit(5)

source_settings()
urlKey = os.environ["url"]
hashKey = os.environ["commitHash"]
repoAndMachineKeys = os.environ["repoOnMachine"].split(",")

class Summarized:
    'Consolidated git details'

    def __init__(self):
        self.infoForRemoteGitUrl = dict()

    def add(self, collection):
        # Key based on remote Git Url
        remoteUrl = collection.pop(urlKey)
        if (self.infoForRemoteGitUrl.get(remoteUrl) == None):
            self.infoForRemoteGitUrl[remoteUrl] = dict()

        # Key based on current commit hash
        commitHash = collection.pop(hashKey)
        if (self.infoForRemoteGitUrl.get(remoteUrl).get(commitHash) == None):
            self.infoForRemoteGitUrl.get(remoteUrl)[commitHash] = RepoDetails()

        # Write the remaining values.
        self.infoForRemoteGitUrl.get(remoteUrl).get(commitHash).add(collection)

class RepoDetails:
    def __init__(self):
        self.repoLocation = list()
        self.repoCurrentCode = None

    def add(self, collection):
        # Always add file system details and machine information for a given repo.
        newRepoLocation = { repoKey: collection.pop(repoKey) for repoKey in repoAndMachineKeys }
        self.repoLocation.append(newRepoLocation)

        # Only collect state of repo once because
        # we've already keyed on a) remote repo and then b) commit hash.
        # Therefore, these remaining values will be static for any repo.
        if (self.repoCurrentCode == None):
            # We've already been removing the values we don't want (via pop)
            self.repoCurrentCode = collection


condensed = Summarized()
csvFile = open(csvFilePath)
data = csv.DictReader(csvFile)
for row in data:
    row.pop("")
    condensed.add(row)
csvFile.close()

# todo: location
summaryFilePath = "/home/localstepdo/Desktop/shared/stampExample2.json"
#summaryFilePath = os.path.join(os.environ["scriptDir"], "summarized.json")
summaryFile = open(summaryFilePath, "wb")
summary = json.dumps(condensed, default=lambda o: o.__dict__)
summaryFile.write(summary)
summaryFile.close()
