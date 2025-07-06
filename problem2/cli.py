#!/usr/bin/env python3

import os
import sys
import subprocess
import argparse
import shutil
import atexit

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
            # Try to move all processes out of this cgroup (if any still exist)
            # This is important to allow rmdir.
            # Reading 'cgroup.procs' can fail if the cgroup is already empty or gone,
            # so we put it in a try-except.
            pids_moved = []
            try:
                with open(os.path.join(cgroup_path, "cgroup.procs"), 'r') as f:
                    pids_in_cgroup = [p.strip() for p in f.readlines() if p.strip()]
                for pid in pids_in_cgroup:
                    try:
                        with open(os.path.join(CGROUP_MEMORY_BASE, "cgroup.procs"), 'w') as f: # Write to root cgroup
                            f.write(pid)
                        pids_moved.append(pid)
                    except Exception:
                        pass # PID might have exited
            except FileNotFoundError:
                pass # cgroup.procs might already be gone if cgroup is being removed
            
            # Now try to remove the cgroup directory
            os.rmdir(cgroup_path)
            print(f"Successfully cleaned up cgroup: {cgroup_path}")
        except OSError as e:
            print(f"Error cleaning up cgroup {cgroup_path}: {e}")
            print("You might need to manually remove it: sudo rmdir <cgroup_path>")
            if pids_moved:
                print(f"PIDs still in cgroup path if manual cleanup is needed: {pids_moved}")
        except Exception as e:
            print(f"An unexpected error occurred during cgroup cleanup: {e}")


def create_container(hostname, memory_limit_mb=None):
    print(f"Creating container with hostname: {hostname} and new namespaces.")

    container_instance_root_fs = os.path.join(CONTAINER_ROOTFS_BASE_DIR, f"{hostname}_{os.getpid()}")
    
    # Ensure the base tarball exists
    if not os.path.exists(UBUNTU_ROOTFS_TAR):
        print(f"Error: Ubuntu rootfs tarball not found at {UBUNTU_ROOTFS_TAR}")
        print("Please run 'sudo docker pull ubuntu:20.04 && sudo docker create --name temp_ubuntu ubuntu:20.04 /bin/bash && sudo docker export temp_ubuntu -o ubuntu_20.04_rootfs.tar && sudo docker rm temp_ubuntu' to create it.")
        sys.exit(1)

    print(f"Preparing root filesystem at: {container_instance_root_fs}")
    os.makedirs(container_instance_root_fs, exist_ok=True)
    
    try:
        subprocess.run(["sudo", "tar", "-xf", UBUNTU_ROOTFS_TAR, "-C", container_instance_root_fs], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error extracting rootfs tarball: {e}")
        sys.exit(1)

    # Copy /etc/resolv.conf from host to container's rootfs for DNS resolution (still useful for future networking)
    container_resolv_conf = os.path.join(container_instance_root_fs, "etc", "resolv.conf")
    try:
        shutil.copy("/etc/resolv.conf", container_resolv_conf)
        print(f"Copied /etc/resolv.conf to {container_resolv_conf}")
    except Exception as e:
        print(f"Warning: Could not copy /etc/resolv.conf to container: {e}")
        print("Container might have no internet access.")


    # --- Copy memory_hog (compiled C executable) into the container's rootfs ---
    memory_hog_source = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory_hog")
    memory_hog_dest_dir = os.path.join(container_instance_root_fs, "usr", "local", "bin")
    os.makedirs(memory_hog_dest_dir, exist_ok=True)
    try:
        shutil.copy(memory_hog_source, memory_hog_dest_dir)
        os.chmod(os.path.join(memory_hog_dest_dir, "memory_hog"), 0o755)
        print(f"Copied memory_hog to {memory_hog_dest_dir} and made it executable.")
    except FileNotFoundError:
        print(f"Error: {memory_hog_source} not found. Did you compile memory_hog.c? Memory test might not work.")
        sys.exit(1)
    except Exception as e:
        print(f"Warning: Could not copy memory_hog to container: {e}")
    # --- End copy memory_hog ---


    # Setup Cgroups for Memory Limit (BONUS)
    cgroup_name = f"mycontainer_{hostname}_{os.getpid()}" # Unique name for this cgroup instance
    cgroup_full_path = os.path.join(CGROUP_MEMORY_BASE, cgroup_name) # Full path on the host cgroupfs
    cgroup_spec = f"memory:/{cgroup_name}" # The string format for cgexec

    if memory_limit_mb:
        memory_limit_bytes = memory_limit_mb * 1024 * 1024 # Convert MB to Bytes
        print(f"Applying memory limit: {memory_limit_mb}MB ({memory_limit_bytes} bytes) using cgroup: {cgroup_full_path}")

        try:
            # Create the cgroup directory on the host's cgroupfs
            os.makedirs(cgroup_full_path, exist_ok=True)

            # Set the memory limit
            with open(os.path.join(cgroup_full_path, "memory.limit_in_bytes"), 'w') as f:
                f.write(str(memory_limit_bytes))
            
            # Register cleanup function to be called on script exit
            atexit.register(cleanup_cgroup, cgroup_full_path)

        except OSError as e:
            print(f"Warning: Could not set memory limit using cgroups: {e}")
            print(f"Attempted cgroup path: {cgroup_full_path}")
            memory_limit_mb = None # Disable memory limit if setup failed
        except Exception as e:
            print(f"An unexpected error occurred during cgroup setup: {e}")
            memory_limit_mb = None # Disable memory limit if setup failed

    # Construct the command to be executed inside the new namespaces
    # This command string will be passed to /bin/sh -c
    inner_container_setup_and_shell_command = (
        f"hostname {hostname} && "
        f"mount --make-rprivate / && "
        f"chroot {container_instance_root_fs} /bin/bash -c \"" # Start bash in chroot
            f"mount -t proc proc /proc && "  # Explicitly mount /proc
            f"mount -t sysfs sys /sys && "  # Mount sysfs
            f"mount -t devtmpfs udev /dev && " # Mount dev
            f"/bin/bash" # The final shell inside the container
        f"\""
    )

    # Base unshare command.
    unshare_base_cmd = [
        "sudo", "unshare",
        "--uts",
        "--pid",
        "--mount",
        "--net",
        "--fork",
    ]

    # Decide the final command that unshare will execute.
    # If memory limit is set, wrap the inner command with `cgexec`.
    # `cgexec` needs to be accessible in the PATH of the *host's* root user.
    # We pass the cgroup spec string directly to `cgexec`.
    command_to_execute_by_unshare = inner_container_setup_and_shell_command

    if memory_limit_mb:
        # Wrap the core command with cgexec.
        # This means `unshare` will execute `sh -c "cgexec -g ..."`
        command_to_execute_by_unshare = f"cgexec -g {cgroup_spec} {inner_container_setup_and_shell_command}"
        print(f"Note: Wrapping inner command with cgexec: {command_to_execute_by_unshare}")


    # Final unshare command string
    unshare_cmd = unshare_base_cmd + ["/bin/sh", "-c", command_to_execute_by_unshare]

    print(f"Executing: {' '.join(unshare_cmd)}")
    try:
        # Replace the current Python process with the constructed unshare command.
        os.execvp(unshare_cmd[0], unshare_cmd)
    except OSError as e:
        print(f"Error executing unshare: {e}")
        sys.exit(1)


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