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
csvFilePath = "/home/localstepdo/Desktop/shared/example.csv" # sys.argv[1] #todo:

if (not os.path.isfile(csvFilePath)):
    print("Path {} is not a file".format(csvFilePath))
    exit(5)

source_settings()
listKey = os.environ["gitAll"]
urlKey = os.environ["url"]
hashKey = os.environ["commitHash"]
gitDetailsKey = os.environ["outputPrefix"]
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

    # Expand dictionarists so that keys have consistent name.
    def getJsonObject(self):
        return {
            "todo" : "counts? lists? etc", #todo:
            listKey: [ { urlKey: key, gitDetailsKey: self.getJsonObjHelper(value) } for key,value in self.infoForRemoteGitUrl.items() ]
        }
    def getJsonObjHelper(self, dictObj):
            return [{ hashKey: key, "repo": value } for key,value in dictObj.items() ]

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

#todo: start clock to read csv
condensed = Summarized()
csvFile = open(csvFilePath)
data = csv.DictReader(csvFile)
for row in data:
    # Remove empty column created by trailing comma.
    row.pop("")
    # Push row into summarized object.
    condensed.add(row)
csvFile.close()
#todo: stop clock

# todo: location
summaryFilePath = "/home/localstepdo/Desktop/shared/example.json"
#summaryFilePath = os.path.join(os.environ["scriptDir"], "summarized.json")

#todo: start clock to write json
summaryFile = open(summaryFilePath, "wb")
summary = json.dumps(condensed.getJsonObject(), default=lambda o: o.__dict__)
summaryFile.write(summary)
summaryFile.close()
#todo: log("summarized resuls can be found in:", summaryFilePath)
#todo: stop clock
