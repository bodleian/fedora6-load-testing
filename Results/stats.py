import os
import subprocess
from statistics import mean, median

# hwType = "default-hardware"
# hwType = "new1PBDrive"
hwType = "uploadByExternalContent"

description = {}  # Name of what to do
description["Metadata"] = "Creating metadata object"
description["Binary"] = "Creating binary file object"
description["LargeBinary"] = "Creating large binary file object"
description["CplxBinary"] = "Creating complex binary file object"
description["VeryLargeBinary"] = "Creating very large binary file object"


nJobs = 3000
nThreads = [10, 5, 3, 1]
work = "Metadata"
work = "Binary"
work = "LargeBinary"
work = "CplxBinary"
work = "VeryLargeBinary"

# default_settings  : Default settings
# increase_java_mem : java : mem+
# java_mem_threads  : java : mem+, threads
# update-3Jan2023   : java : mem++, psql tune
# update-5Jan2023   : java : mem++, threads

# setups = ["default_settings", "increase_java_mem", "update-3Jan2023", "update-5Jan2023", "java_mem_threads"]
# setups = ["default_settings", "increase_java_mem", "java_mem_threads"]
setups = ["java_mem_threads", "update-3Jan2023", "update-5Jan2023"]
# setups = ["update-3Jan2023"]

for nThread in nThreads:
    # print(f"\nNumber of threads : {nThread}\n")
    print(f"\n")
    for setup in setups:
        myCSV = f"{hwType}/{setup}/results_{nJobs}_{nThread}/myResults_J{nJobs}-T{nThread}.csv"

        command = ["grep", description[work], myCSV]
        process = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        s = process.stdout.readlines()
        times = []
        for line in s:
            times.append(float(line.strip().decode().split(", ")[7]))

        mybuffer = []
        with open(myCSV, "r") as file_csv:
            mybuffer = file_csv.readlines()
        tStart = mybuffer[1].split(",")[5].strip()
        tEnd = mybuffer[-1].split(",")[6].strip()
        jobTime = float(tEnd) - float(tStart)

        jobTime2 = 0.0
        tList = []
        kount = 0
        for line in mybuffer:
            kount = kount + 1
            if kount == 1:
                continue # Just skip the first line
            words = len(line.split(","))
            tt = float(line.split(",")[7].strip())
            jobTime2 = jobTime2 + tt
            tList.append(tt)

        # print(f"{setup} {min(times)} {max(times)} {mean(times)} {median(times)}")
        print(f"{min(times)} {max(times)} {mean(times)} {median(times)}")
        # print(f"{min(times)} {max(times)} {mean(times)} {median(times)} {jobTime}")
        # print(f"{jobTime}  {jobTime2}  {mean(tList)}  {median(tList)}")
