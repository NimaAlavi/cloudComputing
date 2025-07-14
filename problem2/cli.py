#!/usr/bin/env python3

import os
import sys
import subprocess
import argparse
import shutil

# Path to the base Ubuntu 20.04 rootfs tarball
UBUNTU_ROOTFS_TAR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ubuntu_20.04_rootfs.tar")
CONTAINER_ROOTFS_BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "container_rootfses")

# Base directory for memory cgroups
CGROUP_MEMORY_BASE = "/sys/fs/cgroup/memory"

def cleanup_cgroup(cgroup_path):
    """Cleans up the created cgroup directory."""
    if os.path.exists(cgroup_path):
        print(f"Cleaning up cgroup: {cgroup_path}")
        try:
            # Move any remaining processes to the root cgroup
            try:
                with open(os.path.join(cgroup_path, "cgroup.procs"), 'r') as f:
                    pids = [p.strip() for p in f.readlines() if p.strip()]
                for pid in pids:
                    try:
                        with open(os.path.join(CGROUP_MEMORY_BASE, "cgroup.procs"), 'w') as f:
                            f.write(pid)
                    except Exception:
                        pass  # PID might have exited
            except FileNotFoundError:
                pass  # Cgroup might already be empty

            os.rmdir(cgroup_path)
            print(f"Successfully cleaned up cgroup: {cgroup_path}")
        except OSError as e:
            print(f"Error cleaning up cgroup {cgroup_path}: {e}")
            print(f"You might need to manually remove it: sudo rmdir {cgroup_path}")
        except Exception as e:
            print(f"Unexpected error during cgroup cleanup: {e}")

def create_container(hostname, memory_limit_mb=None):
    print(f"Creating container with hostname: {hostname} and new namespaces.")

    container_instance_root_fs = os.path.join(CONTAINER_ROOTFS_BASE_DIR, f"{hostname}_{os.getpid()}")

    # Check if required files exist
    if not os.path.exists(UBUNTU_ROOTFS_TAR):
        print(f"Error: Ubuntu rootfs tarball not found at {UBUNTU_ROOTFS_TAR}")
        print("Please run: sudo docker pull ubuntu:20.04 && sudo docker create --name temp_ubuntu ubuntu:20.04 /bin/bash && sudo docker export temp_ubuntu -o ubuntu_20.04_rootfs.tar && sudo docker rm temp_ubuntu")
        sys.exit(1)

    memory_hog_source = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory_hog")
    if not os.path.exists(memory_hog_source):
        print(f"Error: {memory_hog_source} not found. Please compile memory_hog.c with: gcc -o memory_hog memory_hog.c")
        sys.exit(1)

    # Prepare root filesystem
    print(f"Preparing root filesystem at: {container_instance_root_fs}")
    os.makedirs(container_instance_root_fs, exist_ok=True)
    
    try:
        subprocess.run(["tar", "-xf", UBUNTU_ROOTFS_TAR, "-C", container_instance_root_fs], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error extracting rootfs tarball: {e}")
        sys.exit(1)

    # Copy /etc/resolv.conf for DNS
    container_resolv_conf = os.path.join(container_instance_root_fs, "etc", "resolv.conf")
    try:
        shutil.copy("/etc/resolv.conf", container_resolv_conf)
        print(f"Copied /etc/resolv.conf to {container_resolv_conf}")
    except Exception as e:
        print(f"Warning: Could not copy /etc/resolv.conf: {e}")

    # Copy memory_hog to container
    memory_hog_dest_dir = os.path.join(container_instance_root_fs, "usr", "local", "bin")
    os.makedirs(memory_hog_dest_dir, exist_ok=True)
    try:
        shutil.copy(memory_hog_source, memory_hog_dest_dir)
        os.chmod(os.path.join(memory_hog_dest_dir, "memory_hog"), 0o755)
        print(f"Copied memory_hog to {memory_hog_dest_dir}")
    except Exception as e:
        print(f"Warning: Could not copy memory_hog: {e}")

    # Setup cgroups for memory limit
    cgroup_name = f"mycontainer_{hostname}_{os.getpid()}"
    cgroup_full_path = os.path.join(CGROUP_MEMORY_BASE, cgroup_name)
    cgroup_spec = f"memory:/{cgroup_name}"

    if memory_limit_mb:
        memory_limit_bytes = memory_limit_mb * 1024 * 1024
        print(f"Applying memory limit: {memory_limit_mb}MB ({memory_limit_bytes} bytes) using cgroup: {cgroup_full_path}")
        try:
            os.makedirs(cgroup_full_path, exist_ok=True)
            with open(os.path.join(cgroup_full_path, "memory.limit_in_bytes"), 'w') as f:
                f.write(str(memory_limit_bytes))
        except OSError as e:
            print(f"Error setting memory limit: {e}")
            sys.exit(1)

    # Construct the unshare command
    inner_command = (
        f"hostname {hostname} && "
        f"mount --make-rprivate / && "
        f"chroot {container_instance_root_fs} /bin/bash -c \""
        f"mount -t proc proc /proc && "
        f"mount -t sysfs sys /sys && "
        f"mount -t devtmpfs udev /dev && "
        f"/bin/bash\""
    )

    unshare_base_cmd = [
        "unshare",
        "--uts", "--pid", "--mount", "--net", "--fork",
        "/bin/sh", "-c"
    ]

    command_to_execute = inner_command
    if memory_limit_mb:
        command_to_execute = f"cgexec -g {cgroup_spec} {inner_command}"

    unshare_cmd = unshare_base_cmd + [command_to_execute]

    print(f"Executing: {' '.join(unshare_cmd)}")
    try:
        subprocess.run(unshare_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing unshare: {e}")
        sys.exit(1)
    finally:
        if memory_limit_mb:
            cleanup_cgroup(cgroup_full_path)

def main():
    parser = argparse.ArgumentParser(description="A very simple container runtime.")
    parser.add_argument("hostname", help="Hostname for the new container.")
    parser.add_argument("-m", "--memory-limit", type=int, help="Memory limit in MB for the container (BONUS).")

    args = parser.parse_args()

    if os.geteuid() != 0:
        print("This script needs to be run with sudo.")
        sys.exit(1)

    create_container(args.hostname, args.memory_limit)

if __name__ == "__main__":
    main()