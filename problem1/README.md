## Problem 1: Container Networking

### Part 1: Building the Network Topology and Testing Connectivity

In this section, we're going to set up a small yet functional network, mimicking how containers might be isolated but still communicate. Think of each "node" and the "router" as individual containers, each with its own isolated network space.

[cite_start]The network topology we're building is exactly as shown in Figure 1 of the assignment[cite: 34]: four nodes (`node1`, `node2`, `node3`, `node4`) and a central router connecting them. Two bridges (`br1` and `br2`) are used to link the nodes to the router. [cite_start]All nodes and the router reside in their own distinct network namespaces (not the root namespace) [cite: 35][cite_start], while the bridges are located in the root network namespace[cite: 36].

**How it Works:**

1.  **Topology Creation:**
    To set up this network, we've prepared a script named `create_topology.sh`. [cite_start]This script handles all the heavy lifting: it creates the necessary Network Namespaces, bridges, veth pairs (virtual ethernet cable connections between namespaces and bridges), and assigns all the IP addresses according to the network diagram[cite: 36]. [cite_start]It also configures the default gateway for each node to point to the router's IP address within their respective subnets and enables IP forwarding on the router so it can route packets between the different subnets ($172.0.0.0/24$ and $10.10.1.0/24$)[cite: 39, 40].

    To run this script, you'll need `sudo` privileges as it performs system-level network configurations:

    ```bash
    nima@parsida:~/SDMN/HW2/cloudComputing/problem1$ sudo ./create_topology.sh
    # (Output might be minimal or none, which is normal as commands execute in the background)
    ```

2.  **Connectivity Testing (Ping):**
    [cite_start]Once the network topology is up, it's crucial to verify that everything is working as expected and that nodes can communicate with each other and the router[cite: 38]. For this, we use the `ping_nodes.sh` script. This script takes two parameters: the source node's name and the destination node's name (or IP address).

    * **Ping from `node1` to `router`:**
        This command confirms that `node1` can reach its default gateway (the router).

        ```bash
        nima@parsida:~/SDMN/HW2/cloudComputing/problem1$ sudo bash ping_nodes.sh node1 router
        PING 172.0.0.1 (172.0.0.1) 56(84) bytes of data.
        64 bytes from 172.0.0.1: icmp_seq=1 ttl=64 time=0.057 ms
        64 bytes from 172.0.0.1: icmp_seq=2 ttl=64 time=0.059 ms
        64 bytes from 172.0.0.1: icmp_seq=3 ttl=64 time=0.071 ms
        64 bytes from 172.0.0.1: icmp_seq=4 ttl=64 time=0.081 ms
        64 bytes from 172.0.0.1: icmp_seq=5 ttl=64 time=0.071 ms
        ^C
        --- 172.0.0.1 ping statistics ---
        5 packets transmitted, 5 received, 0% packet loss, time 4157ms
        rtt min/avg/max/mdev = 0.057/0.067/0.081/0.008 ms
        ```
        As you can see, packets were successfully transmitted and received, indicating a healthy connection between `node1` and the `router`.

    * **Ping from `node1` to `node3`:**
        This is a critical test! `node1` and `node3` are located in two different subnets. [cite_start]For them to communicate, packets **must** traverse through the router[cite: 39]. This test verifies that our router is correctly routing packets between these distinct subnets.

        ```bash
        nima@parsida:~/SDMN/HW2/cloudComputing/problem1$ sudo bash ping_nodes.sh node1 node3
        PING 10.10.0.2 (10.10.0.2) 56(84) bytes of data.
        64 bytes from 10.10.0.2: icmp_seq=1 ttl=63 time=0.357 ms
        64 bytes from 10.10.0.2: icmp_seq=2 ttl=63 time=0.064 ms
        64 bytes from 10.10.0.2: icmp_seq=3 ttl=63 time=0.878 ms
        64 bytes from 10.10.0.2: icmp_seq=4 ttl=63 time=0.221 ms
        64 bytes from 10.10.0.2: icmp_seq=5 ttl=63 time=0.085 ms
        ^C
        --- 10.10.0.2 ping statistics ---
        5 packets transmitted, 5 received, 0% packet loss, time 4115ms
        rtt min/avg/max/mdev = 0.064/0.321/0.878/0.297 ms
        ```
        The results clearly show `node1` successfully pinging `node3` (which is in a different subnet), confirming the router's proper functioning in inter-subnet routing.

3.  **Cleaning Up Resources:**
    Once you're done experimenting with the topology, it's good practice to free up system resources by removing the Network Namespaces and Bridges. We use the `cleanup.sh` script for this, which also requires `sudo` privileges:

    ```bash
    nima@parsida:~/SDMN/HW2/cloudComputing/problem1$ sudo ./cleanup.sh
    # (Again, output might be minimal or none)
    ```
