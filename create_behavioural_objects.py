from ocfl_interfaces.fedora.behavioural_objects import BehaviouralObjects
from pprint import pprint
from random import shuffle
import time, datetime
import json
import sys

from threading import Thread

# maxThreads = 1
maxThreads = int(sys.argv[1])
maxJobs = 3000
outFile = f"myResults_J{maxJobs}-T{maxThreads}.csv"
outResultsFile = f"myResults_J{maxJobs}-T{maxThreads}.log"
print(f"Using {maxThreads} threads")

description = {}  # Name of what to do
callFunction = {}  # Module to call
numberOfJobs = {}  # Number of times we want to run this type of upload

types = ["Metadata", "Binary", "LargeBinary", "CplxBinary", "VeryLargeBinary"]
# types = ["Metadata", "Binary", "LargeBinary", "CplxBinary"]
# types = ["Metadata", "Binary"]

# numberOfJobs["Metadata"] = 243
# numberOfJobs["Metadata"] = 244
# numberOfJobs["Metadata"] = 250
numberOfJobs["Metadata"] = 487
description["Metadata"] = "Creating metadata object"
callFunction["Metadata"] = "b.create_metadata_object()"

# numberOfJobs["Binary"] = 250
numberOfJobs["Binary"] = 500
description["Binary"] = "Creating binary file object"
callFunction["Binary"] = "b.create_binary_file_objects()"

# numberOfJobs["LargeBinary"]= 5
numberOfJobs["LargeBinary"]= 10
description["LargeBinary"] = "Creating large binary file object"
callFunction["LargeBinary"] = "b.create_large_binary_file_objects()"

# numberOfJobs["CplxBinary"] = 1
numberOfJobs["CplxBinary"] = 2
description["CplxBinary"] = "Creating complex binary file object"
callFunction["CplxBinary"] = "b.create_complex_binary_file_objects()"

numberOfJobs["VeryLargeBinary"] = 1
description["VeryLargeBinary"] = "Creating very large binary file object"
callFunction["VeryLargeBinary"] = "b.create_very_large_binary_file_objects()"

jobsToRun = []
scaleFactor = round(maxJobs / 500.0)
if maxJobs > 500:
    scaleFactor = round(maxJobs / 1000.0)
for type in types:
    for _ in range(numberOfJobs[type] * scaleFactor):
        jobsToRun.append((description[type], callFunction[type]))
shuffle(jobsToRun)
# jobsToRun = jobsToRun[:maxJobs]
jobsToRun = jobsToRun[:20]

with open(outFile, "w") as file_csv:
    wStr = f"threadID, work, nSteps, finalStatus, stepStatusOR, start_time, end_time, time_diff, location\n"
    file_csv.write(wStr)
# ToDo : Extract time for each of the nSteps


def runTheUpload(thread):
    wait = True
    while wait:
        if len(jobsToRun) == 0:
            print("Nothing more to run ...")
            wait = False
            return
        (myStr, myFun) = jobsToRun.pop()
        # start_time = datetime.datetime.utcnow()
        start_time = time.time()
        print(myStr, myFun)
        results = eval(myFun)
        # pprint(results)
        myOkay = True
        for att in results["msg"]:
            if not att["status"]:
                myOkay = False
                break  # Something went wrong in the upload test

        # end_time = datetime.datetime.utcnow()
        end_time = time.time()
        # print("--- %s seconds ---" % (end_time - start_time))
        nResults = len(results["msg"])
        rStatus = results["status"]
        if len(results.get("msg", [])) > 1:
            rLocation = results["msg"][1].get("location", "")
        # stime = start_time.strftime("%Y:%m:%d-%H:%M:%S.%f")
        # etime = end_time.strftime("%Y:%m:%d-%H:%M:%S.%f")
        tdiff = end_time - start_time

        # wStr = f"{thread}, {myStr}, {nResults}, {rStatus}, {myOkay}, {stime}, {etime}, {tdiff.seconds}.{tdiff.microseconds}\n"
        wStr = f"{thread}, {myStr}, {nResults}, {rStatus}, {myOkay}, {start_time}, {end_time}, {tdiff}, {rLocation}\n"
        with open(outFile, "a") as file_csv:
            file_csv.write(wStr)
        with open(outResultsFile, "a") as f:
            for msg in results.get('msg', []):
                try:
                    msg['body'] = msg['body'].decode()
                except:
                    msg['body'] = ''
            f.write(f"{json.dumps(results)}\n")


b = BehaviouralObjects()

thList = []
for i in range(maxThreads):
    thread = Thread(target=runTheUpload, args=(str(i)))  # Define the transfer
    thList.append(thread)
for thread in thList:
    thread.start()  # Start the transfer
for thread in thList:
    thread.join()  # Wait until the threads finish before going forward
