from ocfl_interfaces.fedora.behavioural_objects import BehaviouralObjects
from pprint import pprint
from random import shuffle, randrange
import time, datetime
import json
import sys
import os

from threading import Thread

# maxThreads = 1
maxThreads = int(sys.argv[1])
maxJobs = 3000
outFile = f"myDownload_J{maxJobs}-T{maxThreads}.csv"
print(f"Using {maxThreads} threads")

types = ["Creating metadata object", "Creating binary file object",
    "Creating large binary file object", "Creating complex binary file object",
    "Creating very large binary file object"]

# Fractions
fractions = {}
fractions["Creating metadata object"] = 0.4
fractions["Creating binary file object"] = 0.4
fractions["Creating large binary file object"] = 0.1
fractions["Creating complex binary file object"] = 0.1
fractions["Creating very large binary file object"] = 0.0

# numbers of jobs
nJobs = {}
sJobs = {}
for type in types:
    nJobs[type] = maxJobs * fractions[type]
    sJobs[type] = 0
if maxJobs >= 100000:
    nJobs["Creating very large binary file object"] = 1

myCSV = f"newhw-1Feb2023-java_mempp_threads/results-resize-CB-VLB_400401_10/myResults_J400401-T10.csv"
mybuffer = []
with open(myCSV, "r") as file_csv:
    mybuffer = file_csv.readlines()

toDownload = []
kount = 0

def fillTheJobs(wk, n):
    if n == 0:
        return
    tmpList = []
    for line in mybuffer:
        wtmp = line.strip().split(",")
        if len(wtmp) != 9:
            print(f"Too few fields. Failed transfer? {len(wtmp)}")
            print(f".... {line}")
            continue
        if wtmp[3] == "False":
            continue
        work = wtmp[1].strip()
        if work == "work": # First line in csv file
            continue
        if work == wk:
            tmpList.append((wtmp[1].strip(), wtmp[-1].strip()))
    for _ in range(int(n)):
        toDownload.append(tmpList[randrange(len(tmpList))])
        sJobs[wk] = sJobs[wk] + 1

for type in types:
    fillTheJobs(type, nJobs[type])

shuffle(toDownload)
jobsToRun = toDownload[:maxJobs]
print(len(jobsToRun))

with open(outFile, "w") as file_csv:
    wStr = f"threadID, work, finalStatus, start_time, end_time, time_diff, URL\n"
    file_csv.write(wStr)
# ToDo : Extract time for each of the nSteps

def runTheDownload(thread):
    wait = True
    while wait:
        if len(jobsToRun) == 0:
            print("Nothing more to run ...")
            wait = False
            return
        (myStr, myURL) = jobsToRun.pop()
        start_time = time.time()
        print(myStr, myURL)
        result = b.download_data(myURL)

        end_time = time.time()
        try :
            rStatus = result["status"]
        except:
            print(result)
            rStatus = True
        tdiff = end_time - start_time

        wStr = f"{thread}, {myStr}, {rStatus}, {start_time}, {end_time}, {tdiff}, {myURL}\n"
        with open(outFile, "a") as file_csv:
            file_csv.write(wStr)

        # Clean up the downloaded json file(s) - only the json files are independent of the source?
        heads = result['body'].decode().split("\n")
        for head in heads:
            line = head.strip()
            if line.startswith("ldp:contains"):
                file = line.split()[1][1:-1].split("/")[-1]
                print(file)
                if file.endswith("json"):
                    os.unlink("/test_data/download_data/" + file)



b = BehaviouralObjects()

thList = []
for i in range(maxThreads):
    thread = Thread(target=runTheDownload, args=(str(i)))  # Define the transfer
    thList.append(thread)
for thread in thList:
    thread.start()  # Start the transfer
for thread in thList:
    thread.join()  # Wait until the threads finish before going forward
