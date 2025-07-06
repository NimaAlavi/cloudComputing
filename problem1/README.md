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

### Part 2: Routing without a Router (Figure 2)

This section explains how to enable communication between the two distinct subnets ($172.0.0.0/24$ and $10.10.0.0/24$) after the central router and its links to the bridges (`br1` and `br2`) are removed, as depicted in Figure 2 of the assignment. Since direct routing through a dedicated router is no longer an option, we need to leverage features within the root network namespace to facilitate inter-subnet communication. No implementation is required for this part.

**Current Scenario (as per Figure 2):**
* `node1` and `node2` are in the $172.0.0.0/24$ subnet, connected to `br1`.
* `node3` and `node4` are in the $10.10.0.0/24$ subnet, connected to `br2`.
* There is no direct connection or routing device between `br1` and `br2`.

**Solution Approach:**

To enable routing between these two isolated subnets in the absence of a dedicated router, we can configure the `root` network namespace to act as a router itself. This involves assigning IP addresses to the bridges in the root namespace, enabling IP forwarding, and utilizing Network Address Translation (NAT) rules to ensure proper packet flow and return paths.

**Detailed Steps and Rules in the Root Namespace (with example commands and outputs):**

First, let's confirm our bridges are up and running in the root namespace. This is typically done after running `create_topology.sh` (and before removing the router, if you were to actually implement this scenario):

```bash
nima@parsida:~/SDMN/HW2/cloudComputing/problem1$ sudo ip link show type bridge
22: br1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group default qlen 1000
    link/ether 86:ea:53:ed:73:04 brd ff:ff:ff:ff:ff:ff
23: br2: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group default qlen 1000
    link/ether 8a:af:91:2f:fe:b6 brd ff:ff:ff:ff:ff:ff
‍‍‍```

The output confirms that both `br1` and `br2` are present and in an `UP` state.

1.  **Assign IP Addresses to Bridges:**
    Each bridge (`br1` and `br2`) must be assigned an IP address within its respective subnet. This time, these IP addresses will reside directly on the bridge interfaces in the `root` network namespace. These IPs will serve as the default gateways for the nodes connected to them.

    * For `br1`:
        ```bash
        nima@parsida:~/SDMN/HW2/cloudComputing/problem1$ sudo ip addr add 172.0.0.1/24 dev br1
        # No direct output on success
        ```
    * For `br2`:
        ```bash
        nima@parsida:~/SDMN/HW2/cloudComputing/problem1$ sudo ip addr add 10.10.0.1/24 dev br2
        # No direct output on success
        ```
    To verify the IP addresses have been successfully assigned to the bridges in the root namespace, you can check:
    ```bash
    nima@parsida:~/SDMN/HW2/cloudComputing/problem1$ ip a show br1
    22: br1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default qlen 1000
        link/ether 86:ea:53:ed:73:04 brd ff:ff:ff:ff:ff:ff
        inet 172.0.0.1/24 scope global br1
           valid_lft forever preferred_lft forever
    # You would see similar output for br2 with its assigned IP.
    ```

2.  **Enable IP Forwarding in the Root Namespace:**
    Just like a dedicated router, the root namespace needs to be configured to allow the forwarding of IP packets between different network interfaces (in this case, between `br1` and `br2`). This is a crucial step for inter-subnet communication.

    ```bash
    nima@parsida:~/SDMN/HW2/cloudComputing/problem1$ sudo sysctl -w net.ipv4.ip_forward=1
    net.ipv4.ip_forward = 1
    ```
    The output `net.ipv4.ip_forward = 1` confirms that IP forwarding has been successfully enabled.

3.  **Configure Default Gateways on Nodes:**
    The default gateway for each node should still point to the IP address of its directly connected bridge in the root namespace. This ensures that any traffic destined for a network outside its local subnet is sent to the respective bridge.
    * For `node1` and `node2`: The default gateway would be `172.0.0.1` (the IP of `br1`).
    * For `node3` and `node4`: The default gateway would be `10.10.0.1` (the IP of `br2`).
    (These routes would have been set up by `create_topology.sh` for the router's IPs. In this scenario without the router, if you were to implement this, you would need to adjust the default routes in the node namespaces to point to these new bridge IPs.)

4.  **Implement Network Address Translation (NAT) with Iptables:**
    When a packet from `node1` (e.g., $172.0.0.2$) needs to reach `node3` (e.g., $10.10.0.2$), it will first be routed to `br1` in the root namespace. For the return traffic to find its way back, and to manage the different subnets, we can use Source Network Address Translation (SNAT) or `MASQUERADE`. This changes the source IP address of outgoing packets from one subnet to the IP address of the bridge in the root namespace when crossing between subnets.

    * Rule for packets going from $172.0.0.0/24$ to $10.10.0.0/24$ (out through br2):
        ```bash
        nima@parsida:~/SDMN/HW2/cloudComputing/problem1$ sudo iptables -t nat -A POSTROUTING -o br2 -j MASQUERADE
        # No direct output on success
        ```
    * Rule for packets going from $10.10.0.0/24$ to $172.0.0.0/24$ (out through br1):
        ```bash
        nima@parsida:~/SDMN/HW2/cloudComputing/problem1$ sudo iptables -t nat -A POSTROUTING -o br1 -j MASQUERADE
        # No direct output on success
        ```
    To verify that the iptables rules have been added, you can list them:
    ```bash
    nima@parsida:~/SDMN/HW2/cloudComputing/problem1$ sudo iptables -t nat -L POSTROUTING -n -v
    # You would see output similar to this, showing your MASQUERADE rules
    Chain POSTROUTING (policy ACCEPT 0 packets, 0 bytes)
     pkts bytes target     prot opt in     out     source               destination
        0     0 MASQUERADE  all  --  * br2     0.0.0.0/0            0.0.0.0/0
        0     0 MASQUERADE  all  --  * br1     0.0.0.0/0            0.0.0.0/0
    ```

**Conclusion:**
By assigning IP addresses directly to the bridges within the root namespace, enabling IP forwarding, and applying appropriate NAT rules using `iptables`, the root network namespace effectively acts as a simple router, allowing full connectivity between the two previously isolated subnets as shown in Figure 2.

### Part 3: Routing across Different Servers (Layer 2) (Figure 3)

This section explains how to enable communication between network namespaces that are located on different physical or virtual servers, assuming these servers can see each other at Layer 2 (e.g., they are on the same local area network or connected via a switch). No implementation is required for this part.

**Current Scenario (as per Figure 3):**
* **Server 1:** Hosts `node1` ($172.0.0.2/24$) and `node2` ($172.0.0.3/24$), connected to `br1`.
* **Server 2:** Hosts `node3` ($10.10.0.2/24$) and `node4` ($10.10.0.3/24$), connected to `br2`.
* `Server 1` and `Server 2` are connected via a `switch` at Layer 2, meaning they can directly communicate using MAC addresses within the same broadcast domain. Each server will have a physical/virtual network interface (e.g., `eth0`) connected to this switch.

**Solution Approach:**

To enable routing between namespaces residing on different servers, each server will need to participate in the routing process. This involves configuring the root network namespace of each server to act as a gateway for its local namespaces to reach the other server's networks. We will use the main network interfaces of the servers (connected to the switch) to forward traffic, and typically, we'll need to enable IP forwarding and set up routing rules on each server. Depending on the desired networking model (e.g., direct routing vs. NAT), additional rules like Network Address Translation (NAT) might be required.

**Detailed Steps and Rules on the Servers:**

Let's assume:
* `Server 1` has an external IP address of `192.168.1.10` on its interface connected to the switch (e.g., `eth0`).
* `Server 2` has an external IP address of `192.168.1.20` on its interface connected to the switch (e.g., `eth0`).
* Both `192.168.1.10` and `192.168.1.20` are in the same subnet (e.g., `192.168.1.0/24`) and can directly reach each other over Layer 2.

1.  **Internal Configuration on Each Server:**
    * **On Server 1:**
        * `node1` and `node2` are connected to `br1`. The `br1` on `Server 1` should be configured with an IP address from its local subnet (e.g., `172.0.0.1/24`). The default gateways for `node1` and `node2` should point to this IP (`172.0.0.1`).
    * **On Server 2:**
        * `node3` and `node4` are connected to `br2`. The `br2` on `Server 2` should be configured with an IP address from its local subnet (e.g., `10.10.0.1/24`). The default gateways for `node3` and `node4` should point to this IP (`10.10.0.1`).

2.  **Enable IP Forwarding on Both Servers:**
    Each server needs to be able to forward packets between its internal networks (namespaces via bridges) and its external network interface (connected to the switch).
    * **On Server 1:**
        ```bash
        sudo sysctl -w net.ipv4.ip_forward=1
        ```
    * **On Server 2:**
        ```bash
        sudo sysctl -w net.ipv4.ip_forward=1
        ```

3.  **Configure Routing Rules on Each Server (in their respective Root Namespaces):**
    To allow traffic from namespaces on one server to reach namespaces on the other server, explicit routing rules are required on the root namespace of each server.

    * **On Server 1 (to reach Server 2's subnet):**
        Add a route for the $10.10.0.0/24$ subnet (where `node3` and `node4` reside) to be routed via `Server 2`'s external IP address (`192.168.1.20`), through `Server 1`'s external interface (e.g., `eth0`).
        ```bash
        sudo ip route add 10.10.0.0/24 via 192.168.1.20 dev eth0
        ```

    * **On Server 2 (to reach Server 1's subnet):**
        Add a route for the $172.0.0.0/24$ subnet (where `node1` and `node2` reside) to be routed via `Server 1`'s external IP address (`192.168.1.10`), through `Server 2`'s external interface (e.g., `eth0`).
        ```bash
        sudo ip route add 172.0.0.0/24 via 192.168.1.10 dev eth0
        ```

4.  **Optional: Implement Network Address Translation (NAT) with Iptables:**
    NAT might be necessary if the internal IP address ranges ($172.0.0.0/24$ and $10.10.0.0/24$) are private and not directly routable between the servers' external interfaces, or if you want to conserve IP addresses on the external network. If direct routing is sufficient (i.e., the external network knows how to route to these private subnets on the servers), NAT might not be strictly necessary, but it's a common approach.

    * **On Server 1 (for traffic leaving $172.0.0.0/24$ to cross to $10.10.0.0/24$):**
        This rule translates the source IP of packets originating from `Server 1`'s internal namespaces (e.g., `172.0.0.2`) to `Server 1`'s external IP (`192.168.1.10`) when they exit `eth0` towards `Server 2`.
        ```bash
        sudo iptables -t nat -A POSTROUTING -s 172.0.0.0/24 -o eth0 -j MASQUERADE
        ```

    * **On Server 2 (for traffic leaving $10.10.0.0/24$ to cross to $172.0.0.0/24$):**
        Similarly, this rule translates the source IP of packets originating from `Server 2`'s internal namespaces (e.g., `10.10.0.2`) to `Server 2`'s external IP (`192.168.1.20`) when they exit `eth0` towards `Server 1`.
        ```bash
        sudo iptables -t nat -A POSTROUTING -s 10.10.0.0/24 -o eth0 -j MASQUERADE
        ```
    * **Important Note on NAT:** If NAT is used, the return traffic from the destination node (e.g., `node3` on `Server 2`) will be sent back to the NAT'd IP address (e.g., `192.168.1.10`). The server performing the NAT (e.g., `Server 1`) will then de-NAT the packet and forward it to the original internal IP address (`172.0.0.2`). This is managed automatically by the `MASQUERADE` rule as long as connection tracking is active.

**Conclusion:**
By setting up internal bridge IPs, enabling IP forwarding on both servers, and configuring specific routing rules to point to the other server's external IP for remote subnets, communication can be established between namespaces on different physical or virtual hosts. Optional NAT rules can be added for IP address management or security if required by the network design.