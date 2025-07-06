import os
import sys
import subprocess
import argparse
import shutil # For copying files

# Path to the base Ubuntu 20.04 rootfs tarball
# Make sure this path is correct relative to where your-cli.py is run from
UBUNTU_ROOTFS_TAR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ubuntu_20.04_rootfs.tar")
CONTAINER_ROOTFS_BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "container_rootfses")


def create_container(hostname):
    print(f"Creating container with hostname: {hostname} and new namespaces.")

    # 1. Prepare the container's isolated root filesystem
    # Each container gets its own copy of the rootfs
    container_instance_root_fs = os.path.join(CONTAINER_ROOTFS_BASE_DIR, f"{hostname}_{os.getpid()}")

    # Ensure the base tarball exists
    if not os.path.exists(UBUNTU_ROOTFS_TAR):
        print(f"Error: Ubuntu rootfs tarball not found at {UBUNTU_ROOTFS_TAR}")
        print("Please run 'sudo docker pull ubuntu:20.04 && sudo docker create --name temp_ubuntu ubuntu:20.04 /bin/bash && sudo docker export temp_ubuntu -o ubuntu_20.04_rootfs.tar && sudo docker rm temp_ubuntu' to create it.")
        sys.exit(1)

    print(f"Preparing root filesystem at: {container_instance_root_fs}")
    # Create the directory for this container's rootfs
    os.makedirs(container_instance_root_fs, exist_ok=True)

    # Extract the base tarball into the unique rootfs directory
    try:
        # Use subprocess to extract the tarball as tar command handles sparse files better
        subprocess.run(["sudo", "tar", "-xf", UBUNTU_ROOTFS_TAR, "-C", container_instance_root_fs], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error extracting rootfs tarball: {e}")
        sys.exit(1)


    # 2. Construct the command to be executed inside the new namespaces
    # This command will first set up the mount namespace, then chroot, then run bash.
    # We need to pivot_root (or chroot) and then mount necessary filesystems like /proc, /sys, /dev.
    # It's crucial to set up the mount namespace correctly first.
    # The 'unshare' command's --mount-proc handles /proc, but /sys and /dev need manual mounts.

    # The command string for the inner shell (will be executed after unshare)
    inner_shell_command = (
        f"hostname {hostname} && " # Set hostname in UTS namespace
        f"mount --make-rprivate / && " # Make current mounts private in this namespace

        f"chroot {container_instance_root_fs} /bin/bash -c \"" # Start a new bash within chroot
            f"mount -t proc proc /proc && "  # Explicitly mount /proc
            f"mount -t sysfs sys /sys && "  # Mount sysfs
            f"mount -t devtmpfs udev /dev && " # Mount dev (for devices like /dev/null, /dev/urandom)
            f"/bin/bash" # Finally, run bash inside the chrooted environment
        f"\""
    )

    # Construct the full unshare command
    unshare_cmd = [
        "sudo", "unshare",
        "--uts",    # New UTS namespace
        "--pid",    # New PID namespace
        "--mount",  # New Mount namespace
        "--net",    # New Network namespace
        "--fork",   # Fork into new namespaces
        "--mount-proc", # Automatically mounts /proc in the new PID namespace (crucial for ps fax)
        "/bin/sh", "-c", inner_shell_command
    ]

    print(f"Executing: {' '.join(unshare_cmd)}")
    try:
        os.execvp(unshare_cmd[0], unshare_cmd)
    except OSError as e:
        print(f"Error executing unshare: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="A very simple container runtime.")
    parser.add_argument("hostname", help="Hostname for the new container.")
    # Bonus argument will be added later
    # parser.add_argument("-m", "--memory-limit", type=int, help="Memory limit in MB for the container (BONUS).")

    args = parser.parse_args()

    # You must run this script with sudo to create namespaces
    if os.geteuid() != 0:
        print("This script needs to be run with sudo.")
        sys.exit(1)

    create_container(args.hostname)

if __name__ == "__main__":
    main()