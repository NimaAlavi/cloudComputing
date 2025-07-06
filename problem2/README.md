## Problem 2: Container Runtime

This problem involves implementing a simplified container runtime. This runtime will create isolated environments (containers) using Linux namespaces and a separate root filesystem.

### How to Run:

1.  **Prepare the Ubuntu 20.04 Root Filesystem:**
    First, you need to extract a base Ubuntu 20.04 filesystem. Navigate to the `problem2` directory and run:
    ```bash
    nima@parsida:~/SDMN/HW2/cloudComputing/problem2$ sudo docker pull ubuntu:20.04
    20.04: Pulling from library/ubuntu
    Digest: sha256:8feb4d8ca5354def3d8fce243717141ce31e2c428701f6682bd2fafe15388214
    Status: Image is up to date for ubuntu:20.04
    docker.io/library/ubuntu:20.04
    nima@parsida:~/SDMN/HW2/cloudComputing/problem2$ sudo docker create --name temp_ubuntu ubuntu:20.04 /bin/bash
    d45376603ceeb82f9ca2087c27f5430e72c333af338c2b6e8f7875d66e8e796b
    # Note: The container name created was 'temp_ubuntu', not 'my_ubuntu_temp'.
    # Ensure you use the correct name in the export command.
    nima@parsida:~/SDMN/HW2/cloudComputing/problem2$ sudo docker export temp_ubuntu -o ubuntu_20.04_rootfs.tar
    # No direct output on success, but ubuntu_20.04_rootfs.tar should be created.
    nima@parsida:~/SDMN/HW2/cloudComputing/problem2$ sudo docker rm temp_ubuntu
    temp_ubuntu
    ```
    This creates `ubuntu_20.04_rootfs.tar` in your `problem2` directory.

2.  Make sure the `your-cli.py` script is executable:
    ```bash
    chmod +x your-cli.py
    ```
3.  Run the CLI with `sudo` and provide a hostname:
    ```bash
    sudo python3 ./your-cli.py <your-desired-hostname>
    # Example:
    # nima@parsida:~/SDMN/HW2/cloudComputing/problem2$ sudo python3 ./cli.py myubuntucontainer
    ```

**Demonstration of Namespace and Filesystem Isolation:**

After running the command, you should enter a new bash shell. Inside this new shell, you can verify the isolation:

* **Verify Container Creation and Root Filesystem Preparation:**
    ```bash
    nima@parsida:~/SDMN/HW2/cloudComputing/problem2$ sudo python3 ./cli.py myubuntucontainer
    Creating container with hostname: myubuntucontainer and new namespaces.
    Preparing root filesystem at: /home/nima/SDMN/HW2/cloudComputing/problem2/container_rootfses/myubuntucontainer_9792
    Executing: sudo unshare --uts --pid --mount --net --fork /bin/sh -c hostname myubuntucontainer && mount --make-rprivate / && chroot /home/nima/SDMN/HW2/cloudComputing/problem2/container_rootfses/myubuntucontainer_9792 /bin/bash -c "mount -t proc proc /proc && mount -t sysfs sys /sys && mount -t devtmpfs udev /dev && /bin/bash"
    ```
    You will then be dropped into the container's shell prompt (e.g., `root@myubuntucontainer:/#`).

* **Verify Hostname (UTS Namespace):**
    ```bash
    root@myubuntucontainer:/# hostname
    myubuntucontainer
    ```
    The output clearly shows the hostname has been successfully changed to `myubuntucontainer` within its isolated UTS namespace.

* **Verify Root Filesystem (Mount Namespace & Chroot):**
    ```bash
    root@myubuntucontainer:/# ls /
    bin  boot  dev  etc  home  lib  lib32  lib64  libx32  media  mnt  opt  proc  root  run  sbin  srv  sys  tmp  usr  var
    ```
    This output shows the standard directory structure of a Linux distribution, confirming that the container is using its own isolated root filesystem.

    ```bash
    root@myubuntucontainer:/# cat /etc/os-release
    NAME="Ubuntu"
    VERSION="20.04.6 LTS (Focal Fossa)"
    ID=ubuntu
    ID_LIKE=debian
    PRETTY_NAME="Ubuntu 20.04.6 LTS"
    VERSION_ID="20.04"
    HOME_URL="[https://www.ubuntu.com/](https://www.ubuntu.com/)"
    SUPPORT_URL="[https://help.ubuntu.com/](https://help.ubuntu.com/)"
    BUG_REPORT_URL="[https://bugs.launchpad.net/ubuntu/](https://bugs.launchpad.net/ubuntu/)"
    PRIVACY_POLICY_URL="[https://www.ubuntu.com/legal/terms-and-policies/privacy-policy](https://www.ubuntu.com/legal/terms-and-policies/privacy-policy)"
    VERSION_CODENAME=focal
    UBUNTU_CODENAME=focal
    ```
    This confirms the container is indeed running with an Ubuntu 20.04 filesystem.

* **Verify PID 1 (PID Namespace):**
    ```bash
    root@myubuntucontainer:/# ps fax
        PID TTY      STAT   TIME COMMAND
          1 ?        S      0:00 /bin/sh -c hostname myubuntucontainer && mount --make-rprivate / && chroot /home/nima/SDMN/HW2/cloudComputing/problem2/container_rootfses/myubuntucontainer_9792 /bin/bash -c "mount -t proc proc /p
          4 ?        S      0:00 /bin/bash
         13 ?        R+     0:00  \_ ps fax
    ```
    As demonstrated by the `ps fax` output, `/bin/sh` (which then executes the subsequent commands including `/bin/bash`) is running as PID 1 within its isolated PID namespace, fulfilling the requirement for the container's main process to have PID 1.
    *(Note: You might encounter `error: unknown user-defined format specifier "x"` if you type `ps fox`. The correct command is `ps fax`)*

* To exit the container's shell:
    ```bash
    root@myubuntucontainer:/# exit
    exit
    nima@parsida:~/SDMN/HW2/cloudComputing/problem2$
    ```

### Features (Currently Implemented):

* Creates new `net`, `mnt`, `pid`, and `uts` namespaces for the container.
* Sets the specified hostname within the new UTS namespace.
* Ensures the executed shell (`/bin/bash`) runs as PID 1 within its isolated PID namespace by explicitly mounting `/proc` inside the container.
* Provides a separate root filesystem based on Ubuntu 20.04 using `chroot` and `mount --make-rprivate`.
* (Optional Bonus) Limits memory usage of the container.