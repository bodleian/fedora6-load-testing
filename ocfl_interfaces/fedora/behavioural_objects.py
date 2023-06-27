import os.path
import uuid
import time
import subprocess
import random
from .fedora_api import FedoraApi
from test_objects.create_objects import CreateObjects
from os import environ as env


class BehaviouralObjects:
    def __init__(self, test_data_dir="/test_data/download_data", send_content_by_reference=True):
        self.test_data_dir = test_data_dir
        self.send_content_by_reference = send_content_by_reference
        self.final_result = None
        self.fa = FedoraApi()
        self.co = CreateObjects(self.test_data_dir)
        return

    def download_data(self, url):
        final_result = {"status": True, "msg": []}
        return self.fa.get_data(url, dir=self.test_data_dir)

    def update_metadata_object(self, url, upload=True):
        return self.update_file_object(url=url, type="metadata", both=False, upload=upload)

    def update_binary_file_object(self, url, upload=True):
        return self.update_file_object(url=url, type="binary", both=True, upload=upload)

    def update_large_binary_file_object(self, url, upload=True):
        return self.update_file_object(url=url, type="large_binary", both=False, upload=upload)

    def update_complex_binary_file_object(self, url, upload=True):
        return self.update_file_object(url=url, type="complex_binary", both=True, upload=upload)

    def update_very_large_binary_file_object(self, url, upload=True):
        return self.update_file_object(url=url, type="very_large_binary", both=False, upload=upload)

    def update_file_object(self, url, type="binary", both=True, inTransaction=True, upload=False):
        # Metadata file is always updated
        # both = True : One of the binary files is updated
        # upload = True : A new file is uploaded to the container
        final_result = {"status": True, "msg": []}
        if inTransaction:
            result = self.fa.create_transaction()
            final_result = self._collate_results("Start transaction", final_result, result)
            if not final_result["status"]:
                print(f"Problem with fcrepo server? Error creating transaction.")
                return final_result
            atomic_id = result.get("location", None)
            # keep transaction alive
            proc = self._start_keep_alive_subprocess(atomic_id)

        # Get the list of files to update
        res = self.fa.get_list_of_files(url)
        result = res[0]
        listOfFiles = res[1]
        final_result = self._collate_results("GetFileList", final_result, result)

        # Update the files
        kount = 0
        for file in listOfFiles:
            fileName = file.split("/")[-1]

            # Update the metadata file
            if fileName.endswith("json"): # metadata file
                container_id = url.split("/")[-1]
                file_path = self._create_file("metadata")
                with open(file_path, "a") as f:
                    f.write(f"\n{time.time()}")
                result = self.fa.update_file(file, file_path)
                final_result = self._collate_results("metadataUdt", final_result, result)
                continue

            # Update a binary file if needed
            if both and (not fileName.endswith("json")) and kount == 0:
                kount = 1
                if type == "complex_binary":
                    file_path = self._create_file(type, size=1024*1024*1024)
                else:
                    file_path = self._create_file(type)
                with open(file_path, "a") as f:
                    f.write(f"\n{time.time()}")
                result = self.fa.update_file(file, file_path)
                final_result = self._collate_results(f"{type}FUdt", final_result, result)
                continue

        if upload:
            container_id = url.split("/")[-1]
            file_path = self._create_file(type)
            with open(file_path, "a") as f:
                f.write(f"\n{time.time()}")
            result = self.fa.post_file(container_id, file_path)

        if inTransaction:
            # commit the transaction
            print(f"Committing transaction {atomic_id}")
            result = self.fa.commit_transaction(atomic_id)
            final_result = self._collate_results("Commit transaction", final_result, result)
            print("Terminating the keep alive process")
            proc.kill()

        return final_result


    def create_metadata_object(self):
        # Metadata only objects: a single 2Kb metadata file
        container_id = str(uuid.uuid4())
        metadata_file_name = f"ora.ox.ac.uk:uuid:{container_id}.ora2.json"
        files = {metadata_file_name: "metadata"}
        # create object in fedora
        return self._create_object(container_id, files)

    def create_binary_file_objects(self):
        # 2 binary files 5Mb in size and a single metadata file 2Kb in size
        container_id = str(uuid.uuid4())
        # create files
        metadata_file_name = f"ora.ox.ac.uk:uuid:{container_id}.ora2.json"
        files = {metadata_file_name: "metadata"}
        for i in range(2):
            file_name = f"binary_{i}.bin"
            files[file_name] = "binary"
        return self._create_object(container_id, files)

    def create_large_binary_file_objects(self):
        # 5 binary files 1Gb in size and a single metadata file 2Kb in size
        container_id = str(uuid.uuid4())
        # create files
        metadata_file_name = f"ora.ox.ac.uk:uuid:{container_id}.ora2.json"
        files = {metadata_file_name: "metadata"}
        for i in range(5):
            file_name = f"large_binary_{i}.bin"
            files[file_name] = "large_binary"
        return self._create_object(container_id, files)

    def create_complex_binary_file_objects(self):
        # 100 binary files 500Mb in size and a single metadata file 2Kb in size
        number_of_files = 100
        container_id = str(uuid.uuid4())
        # create files
        metadata_file_name = f"ora.ox.ac.uk:uuid:{container_id}.ora2.json"
        files = {metadata_file_name: "metadata"}
        for i in range(number_of_files):
            file_name = f"complex_binary_{i}.bin"
            files[file_name] = "complex_binary"
        return self._create_object(container_id, files)

    def create_very_large_binary_file_objects(self):
        # 1 binary file 256Gb in size and a single metadata file 2Kb in size
        # Testing with size 100 GB
        number_of_files = 1
        container_id = str(uuid.uuid4())
        # create files
        metadata_file_name = f"ora.ox.ac.uk:uuid:{container_id}.ora2.json"
        files = {metadata_file_name: "metadata"}
        for i in range(number_of_files):
            file_name = f"very_large_binary_{i}.bin"
            files[file_name] = "very_large_binary"
        return self._create_object(container_id, files)

    def _create_object(self, container_id, files):
        if self.send_content_by_reference:
            return self._create_object_by_reference(container_id, files)
        else:
            return self._create_object_by_post(container_id, files)

    def _create_object_by_post(self, container_id, files):
        # Create objects by sending the files in the post request
        final_result = {"status": True, "msg": []}
        # Start transaction
        result = self.fa.create_transaction()
        final_result = self._collate_results("Start transaction", final_result, result)
        if not final_result["status"]:
            return final_result
        atomic_id = result.get("location", None)
        # keep transaction alive
        proc = self._start_keep_alive_subprocess(atomic_id)
        # create a container
        result = self.fa.create_container(container_id=container_id, archival_group=True, atomic_id=atomic_id)
        result["ocfl_path"] = self.fa.get_ocfl_object_path(container_id)
        final_result = self._collate_results("Create a container", final_result, result)
        # add files
        for file_location in files:
            # creating a file
            print("Creating file")
            file_path = self._create_file(files[file_location])
            # updating the file with timestamp, so it's different
            with open(file_path, "a") as f:
                f.write(f"\n{time.time()}")
            if files[file_location] == "very_large_binary":
                print("Copying file to server")
                # file is located in test data dir. Need to copy it to shared local data dir
                ans = self.copy_file_to_fedora(file_path)
                copy_proc = ans[0]
                copy_src = ans[1]
                copy_dest = ans[2]
                copy_proc.wait()
                print("Posting file to server")
                result = self.fa.add_external_file(
                    "POST", container_id, file_path, copy_dest, file_location=file_location, atomic_id=atomic_id
                )
                # result = self.fa.add_external_file("POST", container_id, './shared_data/largeFiles.zip', '/data/shared_data/largeFiles.zip', file_location='largeFile.zip',
                #                            atomic_id=atomic_id)

            else:
                # post file
                result = self.fa.post_file(container_id, file_path, file_location=file_location, atomic_id=atomic_id)
            final_result = self._collate_results(f"Add file {file_location}", final_result, result)
        # commit the transaction
        print(f"Committing transaction {atomic_id}")
        result = self.fa.commit_transaction(atomic_id)
        final_result = self._collate_results("Commit transaction", final_result, result)
        print("Terminating the keep alive process")
        proc.kill()
        return final_result

    def _create_object_by_reference(self, container_id, files):
        # Create objects by using external content in Fedora
        final_result = {"status": True, "msg": []}
        # Start transaction
        result = self.fa.create_transaction()
        final_result = self._collate_results("Start transaction", final_result, result)
        if not final_result["status"]:
            return final_result
        atomic_id = result.get("location", None)
        # keep transaction alive
        proc = self._start_keep_alive_subprocess(atomic_id)
        # create a container
        result = self.fa.create_container(container_id=container_id, archival_group=True, atomic_id=atomic_id)
        result["ocfl_path"] = self.fa.get_ocfl_object_path(container_id)
        final_result = self._collate_results("Create a container", final_result, result)
        # add files
        for file_location in files:
            # creating a file
            print("Creating file")
            file_path = self._create_file(files[file_location])
            # updating the file with timestamp, so it's different
            with open(file_path, "a") as f:
                f.write(f"\n{time.time()}")
            if files[file_location] != "metadata":
                print("Posting file to server")
                result = self.fa.add_external_file(
                    "POST", container_id, file_path, file_path, file_location=file_location, atomic_id=atomic_id
                )

            else:
                # post file
                result = self.fa.post_file(container_id, file_path, file_location=file_location, atomic_id=atomic_id)
            final_result = self._collate_results(f"Add file {file_location}", final_result, result)
        # commit the transaction
        print(f"Committing transaction {atomic_id}")
        result = self.fa.commit_transaction(atomic_id)
        final_result = self._collate_results("Commit transaction", final_result, result)
        print("Terminating the keep alive process")
        proc.kill()
        return final_result

    def _collate_results(self, action, final_result, result):
        result["action"] = action
        if not result["status"]:
            final_result["status"] = False
        final_result["msg"].append(result)
        return final_result

    def _create_file(self, file_type, size=0):
        if file_type == "metadata":
            return self.co.create_metadata_file()
        elif file_type == "binary":
            return self.co.create_binary_file()
        elif file_type == "large_binary":
            return self.co.create_large_binary_file()
        elif file_type == "complex_binary":
            if size > 0:
                return self.co.create_complex_binary_file(size=size)
            else:
                return self.co.create_complex_binary_file()
        elif file_type == "very_large_binary":
            return self.co.create_very_large_binary_file()

    def _start_keep_alive_subprocess(self, atomic_id):
        cmd = ["python3", "./ocfl_interfaces/fedora/keep_alive.py", atomic_id]
        proc = subprocess.Popen(
            cmd, shell=False, close_fds=True
        )  # stdin=None, stdout=None, stderr=None, close_fds=True)
        return proc

    def copy_file_to_fedora(self, local_file_path):
        file_name = os.path.basename(local_file_path)
        local_dest_path = os.path.join(env["SHARED_DATA_FOLDER_LOCAL"], file_name)
        server_dest_path = os.path.join(env["SHARED_DATA_FOLDER_FCREPO"], file_name)

        if not os.path.exists(local_file_path) and os.path.isfile(local_file_path):
            return False
        cmd = ["scp", local_file_path, local_dest_path]
        proc = subprocess.Popen(cmd, shell=False, close_fds=True)
        return (proc, local_dest_path, server_dest_path)
