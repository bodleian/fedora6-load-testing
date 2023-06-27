from ocfl_interfaces.fedora.fedora_api import FedoraApi
import sys
import time


class KeepAlive:
    def __init__(self, atomic_id_uri):
        self.fa = FedoraApi()
        self.atomic_id_uri = atomic_id_uri
        self.atomic_id = self.atomic_id_uri.split("/")[-1]
        # Transactions are automatically closed and rolled back after 3 minutes of inactivity.
        # Setting ping interval 20 2.5 minutes
        self.ping_interval = 150

    def keep_transaction_alive(self):
        wait = True
        while wait:
            print(f"Keeping transaction {self.atomic_id} alive")
            result = self.fa.keep_transaction_alive(self.atomic_id_uri)
            if not result["status"]:
                wait = False
            time.sleep(self.ping_interval)
        print(f"transaction {self.atomic_id.split('/')[-1]} is done")
        return


if __name__ == "__main__":
    # Atomic ID URI
    atomic_id = sys.argv[1]
    ka = KeepAlive(atomic_id)
    ka.keep_transaction_alive()
    
