#!/usr/bin/python
# Copyright (c) Microsoft Corporation. All Rights Reserved.
# Licensed under the MIT license. See LICENSE file on the project webpage for details.

import os
import sys
import csv
import json
from urlparse import urlparse,urljoin
from helpers.sourceSettings import source_settings

# Expects directory as an argument.
if (len(sys.argv) != 2):
    print("Path Expected")
    exit(3)
csvFilePath = "/home/localstepdo/e/getAllGit/summarizedWebView/example2.csv" # sys.argv[1] #todo:

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
        remoteUrl = collection.pop(urlKey).lower()

        if (not urlparse(remoteUrl).scheme):
            # Ignore local repositories
            return

        if (self.infoForRemoteGitUrl.get(remoteUrl) == None):
            self.infoForRemoteGitUrl[remoteUrl] = dict()

        # Key based on current commit hash
        commitHash = collection.pop(hashKey).upper()
        if (self.infoForRemoteGitUrl.get(remoteUrl).get(commitHash) == None):
            self.infoForRemoteGitUrl.get(remoteUrl)[commitHash] = RepoDetails()

        # Write the remaining values.
        self.infoForRemoteGitUrl.get(remoteUrl).get(commitHash).add(collection)

    # Expand dictionarists so that keys have consistent name.
    def getJsonObject(self):
        return [{ urlKey: UrlDetails(key), gitDetailsKey: self.getJsonObjHelper(value) } for key,value in self.infoForRemoteGitUrl.items() ]
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
        # Therefore, these remaining values will be static for any repo so only store once.
        if (self.repoCurrentCode == None):
            # We've already removed all other values so a normal assignment would work,
            # but we're using this opportunity to incorporate newlines in the markup.
            self.repoCurrentCode = { key: value.replace('\n', '<br/>') for key,value in collection.items() }

class UrlDetails:
    def __init__(self, url):
        parsed = urlparse(url)
        parts = parsed.path.split('.')
        self.short = parsed.netloc + parts[0]
        self.full = urljoin(url, parts[0])

        parts = parts[0].split('/')
        self.org = parts[1]
        self.project = parts[2]

#todo: start clock to read csv
condensed = Summarized()
csvFile = open(csvFilePath)
data = csv.DictReader(csvFile)
for row in data:
    # Remove empty column created by trailing comma.
    if (row.get("") != None):
        row.pop("")

    # Push row into summarized object.
    condensed.add(row)
csvFile.close()
#todo: stop clock

# todo: location
summaryFilePath = "/home/localstepdo/e/getAllGit/summarizedWebView/example2b.json"
#summaryFilePath = os.path.join(os.environ["scriptDir"], "summarized.json")

#todo: start clock to write json
summaryFile = open(summaryFilePath, "wb")
summary = json.dumps(condensed.getJsonObject(), default=lambda o: o.__dict__)
summaryFile.write(summary)
summaryFile.close()
#todo: log("summarized resuls can be found in:", summaryFilePath)
#todo: stop clock
