import os
import time
import subprocess

# nJobs = 500
nJobs = 3000
# outputDir = "java_mem_threads"
# outputDir = "default_settings"
# outputDir = "increase_java_mem"
# outputDir = "update-5Jan2023"
outputDir = "update-3Jan2023"
def runOneSet(nThreads):
    print(f"Running job with {nThreads} threads")
    resDir = f"results_{nJobs}_{nThreads}"
    os.system(f"mkdir {resDir}")

    # Run system load check in the background, wait for 30 seconds before starting
    command = ["python3", "systemLoad.py"]
    sysProcess = subprocess.Popen(command)
    time.sleep(30)

    # Run the upload test
    logFile = f"create_behavioural_objects-{nJobs}-{nThreads}.log"
    f = open(logFile, "w")
    command = ["python3", "create_behavioural_objects.py", str(nThreads)]
    process = subprocess.Popen(command, stdout=f)
    process.communicate() # should wait until the above process finishes

    # Wait until system load process exits
    sysProcess.wait()

    # Move the outputs to the correct directory
    command = f"mv myLoad.csv {resDir}/"
    os.system(command)
    command = f"mv myResults_J{nJobs}-T{nThreads}.csv {resDir}/"
    os.system(command)
    command = f"mv myResults_J{nJobs}-T{nThreads}.log {resDir}/"
    os.system(command)
    command = f"mv {logFile} {resDir}/"
    os.system(command)
    command = f"mv {resDir} {outputDir}"
    os.system(command)

    # sleep for 2 minutes before returning
    time.sleep(120)
    print(f"runOneSet finished {nJobs} - {nThreads} ...")
    return resDir

os.system(f"mkdir {outputDir}")
# runOneSet(10)
runOneSet(5)
runOneSet(3)
runOneSet(1)
