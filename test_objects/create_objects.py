#!/usr/bin/python
import os
import subprocess
import shutil
import math
# from dotenv import load_dotenv
from os import environ as env
import uuid

class CreateObjects:
    def __init__(self, test_data_dir):
        # load_dotenv()
        if not os.path.isdir(test_data_dir):
            os.makedirs(test_data_dir, exist_ok=True)
        self.test_data_dir = test_data_dir

    def create_file(self, file_name, file_size=0, timeout=15*60*60):
        # Create a file with given name and size (in bytes)
        if file_size <= 0:
            return
        filePath = os.path.join(self.test_data_dir, str(uuid.uuid4()) + file_name)
        # If the file with the same name and approximately same size already exists, just return that
        if os.path.exists(filePath):
            fS = os.stat(filePath).st_size
            if (file_size * 0.90) <= fS <= (file_size * 1.1):
                return filePath
        if file_size < (10 * 1024 * 1024):
            with open(filePath, "wb") as f:
                f.write(os.urandom(file_size))
        else:
            count = math.ceil(file_size / (10*1024*1024))
            cmd = ["dd", "if=/dev/urandom", f"of={filePath}", "bs=10M", f"count={count}"]
            print(cmd)
            proc = subprocess.Popen(cmd, shell=False, close_fds=True)
            proc.wait(timeout=timeout)
        return filePath

    def create_metadata_file(self, file_name="metadata.bin"):
        # a single 2Kb metadata file
        return self.create_file(file_name, 2 * 1024)

    def create_binary_file(self, file_name="binary.bin"):
        # 5Mb in size
        return self.create_file(file_name, 5 * 1024 * 1024)

    def create_complex_binary_file(self, file_name="complexBinary.bin", size= 500 * 1024 * 1024):
        # 500Mb in size
        # Change to 50MB in size for disk space reasons
        return self.create_file(file_name, size)

    def create_large_binary_file(self, file_name="largeBinary.bin"):
        # 1Gb in size
        return self.create_file(file_name, 1 * 1024 * 1024 * 1024)

    def create_very_large_binary_file(self, file_name="veryLargeBinary.bin"):
        # 256Gb in size
        return self.create_file(file_name, int( env['VERY_LARGE_FILE_SIZE']))

    def cleanup(self, dir_to_clean=None):
        if dir_to_clean and os.path.isdir(dir_to_clean) and dir_to_clean.startswith(self.test_data_dir):
            shutil.rmtree(dir_to_clean)
        elif not dir_to_clean:
            shutil.rmtree(self.test_data_dir)
        return
