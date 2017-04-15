#!/usr/bin/python
# Copyright (c) Microsoft Corporation. All Rights Reserved.
# Licensed under the MIT license. See LICENSE file on the project webpage for details.

import os
import sys
import csv
#import pandas
import sourceSettings

# Expects directory as an argument.
# todo: consider using getopt or argparse
if (len(sys.argv) != 2):
    print("Path Expected")
    exit(3)
csvFilePath = "/home/localstepdo/Desktop/shared/devEnvExample2.csv"
# "C:\\Users\\stepdo\\Desktop\\files\\devEnvExample2.csv" # sys.argv[1] #todo:

if (not os.path.isfile(csvFilePath)):
    print("Path {} is not a file".format(csvFilePath))
    exit(5)

csvFile = open(csvFilePath)
data = csv.DictReader(csvFile)
for row in data:
    print(row)
csvFile.close()