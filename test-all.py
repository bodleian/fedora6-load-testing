from ocfl_interfaces.fedora.behavioural_objects import BehaviouralObjects
from pprint import pprint
from random import shuffle, random
import time, datetime
import json
import sys

from threading import Thread

# Aim : 75% download. 12.5% upload. 12.5% update.
#   Also, if it is a metadata object, only download is done.
#   So, revised numbers :
#      Metadata object : Download (this is about 50% of the data)
#      Else : 60% download, 20% upload, 20% update
#      This will give us the overall numbers at the top (approx)

maxThreads = int(sys.argv[1])
maxJobs = 100000
outFile = f"myFullTest_J{maxJobs}-T{maxThreads}.csv"
print(f"Using {maxThreads} threads")

myCSV = f"newhw-1Feb2023-java_mempp_threads/results-resize-CB-VLB_400401_10/myResults_J400401-T10.csv"
mybuffer = []
with open(myCSV, "r") as file_csv:
    mybuffer = file_csv.readlines()

toDownload = []
kount = 0
for line in mybuffer:
    wtmp = line.strip().split(",")
    if len(wtmp) != 9:
        print(f"Too few fields. Failed transfer? {len(wtmp)}")
        print(f".... {line}")
        continue
    if wtmp[3] == "False":
        continue
    toDownload.append((wtmp[1].strip(), wtmp[-1].strip()))

shuffle(toDownload)
jobsToRun = toDownload[:maxJobs]

with open(outFile, "w") as file_csv:
    wStr = f"threadID, work, type, finalStatus, start_time, end_time, time_diff, URL\n"
    file_csv.write(wStr)
# ToDo : Extract time for each of the nSteps

def runTheProcess(thread):
    wait = True
    while wait:
        if len(jobsToRun) == 0:
            print("Nothing more to run ...")
            wait = False
            return

        (myStr, myURL) = jobsToRun.pop()

        if myStr.startswith("Creating large binary") or myStr.startswith("Creating complex binary") \
           or myStr.startswith("Creating very large binary"):
           continue

        start_time = time.time()
        # print(myStr, myURL)

        xr = random()
        upload = -1
        workType = "Download"
        if xr > 0.25: # 3 / 4
            result = b.download_data(myURL)
        elif xr < 0.125: # 12.5%
            upload = True
            workType = "UpdateUpload"
        else: # 12.5%
            upload = False
            workType = "UpdateOnly"

        # print(f"{workType} {myStr} {myURL}")

        if isinstance(upload, bool):
            if myStr.startswith("Creating metadata"):
                result = b.update_metadata_object(myURL, upload=upload)
            elif myStr.startswith("Creating binary"):
                result = b.update_binary_file_object(myURL, upload=upload)
            elif myStr.startswith("Creating large binary"):
                result = b.update_large_binary_file_object(myURL, upload=upload)
            elif myStr.startswith("Creating complex binary"):
                result = b.update_complex_binary_file_object(myURL, upload=upload)
            elif myStr.startswith("Creating very large binary"):
                result = b.update_very_large_binary_file_object(myURL, upload=upload)
            else:
                print(f"Unknown type : {myStr}")

        end_time = time.time()
        try :
            rStatus = result["status"]
        except:
            print(result)
            rStatus = False #??
        tdiff = end_time - start_time

        if rStatus == False:
            print(result)

        wStr = f"{thread}, {myStr}, {workType}, {rStatus}, {start_time}, {end_time}, {tdiff}, {myURL}\n"
        with open(outFile, "a") as file_csv:
            file_csv.write(wStr)

b = BehaviouralObjects()

thList = []
for i in range(maxThreads):
    thread = Thread(target=runTheProcess, args=(str(i)))  # Define the transfer
    thList.append(thread)
for thread in thList:
    thread.start()  # Start the transfer
for thread in thList:
    thread.join()  # Wait until the threads finish before going forward
