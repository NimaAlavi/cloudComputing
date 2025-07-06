## Problem 2: Container Runtime

This problem involves implementing a simplified container runtime. This runtime will create isolated environments (containers) using Linux namespaces and a separate root filesystem.

### How to Run:

1.  Make sure the `cli.py` script is executable:
    ```bash
    chmod +x cli.py
    ```
2.  Run the CLI with `sudo` and provide a hostname:
    ```bash
    sudo python3 ./cli.py <your-desired-hostname>
    # Example:
    # sudo python3 ./cli.py mycontainer
    ```

**Demonstration of Namespace Isolation:**

After running the command, you should enter a new bash shell. Inside this new shell, you can verify the namespace isolation:

* **Verify Hostname (UTS Namespace):**
    ```bash
    root@mycontainer:/home/nima/SDMN/HW2/cloudComputing/problem2# hostname
    mycontainer
    ```
    The output clearly shows the hostname has been successfully changed to `mycontainer` within its isolated UTS namespace.

* **Verify PID 1 (PID Namespace):**
    ```bash
    root@mycontainer:/home/nima/SDMN/HW2/cloudComputing/problem2# ps fax
        PID TTY      STAT   TIME COMMAND
          1 pts/0    S      0:00 /bin/sh -c hostname mycontainer && /bin/bash
          3 pts/0    S      0:00  \_ /bin/bash
         11 pts/0    R+     0:00   \_ ps fax
    ```
    As demonstrated by the `ps fax` output, `/bin/sh` (which then executes `/bin/bash`) is running as PID 1 within its isolated PID namespace, fulfilling the requirement for the container's main process to have PID 1.

* To exit the container's shell and return to your host system:
    ```bash
    root@mycontainer:/home/nima/SDMN/HW2/cloudComputing/problem2# exit
    exit
    nima@parsida:~/SDMN/HW2/cloudComputing/problem2$
    ```

### Features (Currently Implemented):

* Creates new `net`, `mnt`, `pid`, and `uts` namespaces for the container using `unshare`.
* Sets the specified hostname within the new UTS namespace.
* Ensures the executed shell (`/bin/bash`) runs as PID 1 within its isolated PID namespace.
* (Future) Provides a separate root filesystem based on Ubuntu 20.04.
* (Optional Bonus) Limits memory usage of the container.