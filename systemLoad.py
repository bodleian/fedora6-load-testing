import os
import time
import subprocess
import datetime

today = datetime.datetime.today().strftime("%d%b%Y")
outFile = f"myLoad.csv"

with open(outFile, "w") as file_csv:
    file_csv.write("tTime, Time, loadAvg 1m, loadAvg 5m, loadAvg 15m\n")

wait = True
kount = 0
while wait or kount < 20:
    # Current time
    now = datetime.datetime.utcnow().strftime("%H:%M:%S.%f")
    nowt = time.time()
    # Load
    load = os.getloadavg()
    with open(outFile, "a") as file_csv:
        file_csv.write(f"{nowt}, {now}, {load[0]}, {load[1]}, {load[2]}\n")
    wait = False
    command = ["ps", "fx"]
    process = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)  # , universal_newlines=True)
    s = process.stdout.readlines()
    for proc in s:
        if "create_behavioural" in proc.decode():
            wait = True
            kount = 0
        if "download_behavioural" in proc.decode():
            wait = True
            kount = 0
        if "test-all" in proc.decode():
            wait = True
            kount = 0

    if not wait:
        kount = kount + 1

    time.sleep(10)
