import os
import sys
import subprocess
import argparse

def create_container(hostname):
    print(f"Creating container with hostname: {hostname} and new namespaces.")

    # The 'unshare' command is the easiest way to create new namespaces from Python
    # without complex C bindings or ctypes.
    # We need to run 'unshare' with specific flags for each required namespace.
    # --uts: New UTS namespace (for hostname)
    # --pid: New PID namespace (for PID 1 inside container)
    # --mount: New Mount namespace (for isolated filesystem)
    # --net: New Network namespace (for isolated network)
    # --fork: Forks the process into the new namespaces, so the parent script can continue.
    # --mount-proc: Automatically mounts /proc in the new PID namespace, essential for 'ps fax' to work.

    # The command to execute inside the new namespaces.
    # We wrap it in /bin/sh -c to execute multiple commands sequentially.
    # First, set the hostname in the new UTS namespace.
    # For now, we'll just run /bin/bash after setting hostname.
    # The rootfs setup will be in the next commit.

    container_command = [
        "hostname", hostname, # Set the hostname in the new UTS namespace
        "&&", "/bin/bash"    # Then execute bash
    ]

    # Construct the full unshare command
    unshare_cmd = [
        "sudo", "unshare",
        "--uts",
        "--pid",
        "--mount",
        "--net",
        "--fork",
        "--mount-proc", # Important for PID 1
        "/bin/sh", "-c", " ".join(container_command)
    ]

    print(f"Executing: {' '.join(unshare_cmd)}")
    try:
        # os.execvp replaces the current process with the new one.
        # This means the Python script will be replaced by the unshare command.
        os.execvp(unshare_cmd[0], unshare_cmd)
    except OSError as e:
        print(f"Error executing unshare: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="A very simple container runtime.")
    parser.add_argument("hostname", help="Hostname for the new container.")
    args = parser.parse_args()

    # Ensure the script is run with sudo
    if os.geteuid() != 0:
        print("This script needs to be run with sudo.")
        sys.exit(1)

    create_container(args.hostname)

if __name__ == "__main__":
    main()