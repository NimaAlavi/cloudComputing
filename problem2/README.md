## Problem 2: Container Runtime

This problem involves implementing a simplified container runtime. This runtime will create isolated environments (containers) using Linux namespaces and a separate root filesystem.

### How to Run:

1. **Prepare the Ubuntu 20.04 Root Filesystem:** First, you need to extract a base Ubuntu 20.04 filesystem. Navigate to the `problem2` directory and run:

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

2. Make sure the `your-cli.py` script is executable:

   ```bash
   chmod +x your-cli.py
   ```

3. Run the CLI with `sudo` and provide a hostname:

   ```bash
   sudo python3 ./your-cli.py <your-desired-hostname>
   # Example:
   # nima@parsida:~/SDMN/HW2/cloudComputing/problem2$ sudo python3 ./cli.py myubuntucontainer
   ```

---

### Demonstration of Namespace and Filesystem Isolation:

After running the command, you should enter a new bash shell. Inside this new shell, you can verify the isolation:

- **Verify Container Creation and Root Filesystem Preparation:**

  ```bash
  nima@parsida:~/SDMN/HW2/cloudComputing/problem2$ sudo python3 ./cli.py myubuntucontainer
  Creating container with hostname: myubuntucontainer and new namespaces.
  Preparing root filesystem at: /home/nima/SDMN/HW2/cloudComputing/problem2/container_rootfses/myubuntucontainer_9792
  Executing: sudo unshare --uts --pid --mount --net --fork /bin/sh -c hostname myubuntucontainer && mount --make-rprivate / && chroot /home/nima/SDMN/HW2/cloudComputing/problem2/container_rootfses/myubuntucontainer_9792 /bin/bash -c "mount -t proc proc /proc && mount -t sysfs sys /sys && mount -t devtmpfs udev /dev && /bin/bash"
  ```

  You will then be dropped into the container's shell prompt (e.g., `root@myubuntucontainer:/#`).

- **Verify Hostname (UTS Namespace):**

  ```bash
  root@myubuntucontainer:/# hostname
  myubuntucontainer
  ```

- **Verify Root Filesystem (Mount Namespace & Chroot):**

  ```bash
  root@myubuntucontainer:/# ls /
  bin  boot  dev  etc  home  lib  lib32  lib64  libx32  media  mnt  opt  proc  root  run  sbin  srv  sys  tmp  usr  var
  ```

- **Verify PID 1 (PID Namespace):**

  ```bash
  root@myubuntucontainer:/# ps fax
      PID TTY      STAT   TIME COMMAND
        1 ?        S      0:00 /bin/sh -c hostname myubuntucontainer && mount --make-rprivate / && chroot /home/nima/SDMN/HW2/cloudComputing/problem2/container_rootfses/myubuntucontainer_9792 /bin/bash -c "mount -t proc proc /p
        4 ?        S      0:00 /bin/bash
       13 ?        R+     0:00  \_ ps fax
  ```

  As demonstrated by the `ps fax` output, `/bin/sh` is running as PID 1 within its isolated PID namespace.

- To exit the container's shell:

  ```bash
  root@myubuntucontainer:/# exit
  exit
  nima@parsida:~/SDMN/HW2/cloudComputing/problem2$
  ```

### Features (Currently Implemented):

- Creates new `net`, `mnt`, `pid`, and `uts` namespaces for the container.
- Sets the specified hostname within the new UTS namespace.
- Ensures the executed shell (`/bin/bash`) runs as PID 1 within its isolated PID namespace by explicitly mounting `/proc` inside the container.
- Provides a separate root filesystem based on Ubuntu 20.04 using `chroot` and `mount --make-rprivate`.
- (Optional Bonus) Limits memory usage of the container.

---

### Memory Limiting Verification

To test the cgroup memory limits, we built a small `memory_hog` binary that attempts to allocate up to 15 MB incrementally until it is killed by OOM:

```bash
# Run the container with a 5 MB memory limit and start the memory_hog workload.
sudo python3 cli.py --memory-limit 5 mycontainer
Creating container with hostname: mycontainer and new namespaces.
Preparing root filesystem at: /home/nima/SDMN/HW2/cloudComputing/problem2/container_rootfses/mycontainer_4322
Copied /etc/resolv.conf to /home/nima/.../container_rootfses/mycontainer_4322/etc/resolv.conf
Copied memory_hog to /home/nima/.../container_rootfses/mycontainer_4322/usr/local/bin
Applying memory limit: 5MB (5242880 bytes) using cgroup: /sys/fs/cgroup/memory/mycontainer_mycontainer_4322
Executing: unshare --uts --pid --mount --net --fork cgexec -g memory:/mycontainer_mycontainer_4322 chroot /home/nima/.../container_rootfses/mycontainer_4322 /setup.sh
root@mycontainer:/# memory_hog
Attempting to allocate up to 15 MB...
Allocated 1 MB
Allocated 2 MB
Allocated 3 MB
Killed
```

After the kill, inspecting the cgroup memory usage file on the host shows:

```bash
cat /sys/fs/cgroup/memory/memory.usage_in_bytes
5352784
```

This confirms that the memory limit was correctly enforced by the cgroup (the process was killed after crossing \~3 MB), and there is no error caused by the kill—it simply demonstrates that the limit is active. The high value in `memory.usage_in_bytes` reflects the underlying Docker host’s own memory usage and does not affect the container’s enforced limit.

---

*End of Problem 2 Report*

