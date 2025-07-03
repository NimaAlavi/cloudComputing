# Create network namespaces
sudo ip netns add node1
sudo ip netns add node2
sudo ip netns add node3
sudo ip netns add node4
sudo ip netns add router

# Create bridges in the root namespace
sudo ip link add br1 type bridge
sudo ip link add br2 type bridge
sudo ip link set br1 up
sudo ip link set br2 up

# Create veth pairs and connect nodes to bridges
sudo ip link add veth_node1 type veth peer name veth_br1
sudo ip link set veth_node1 netns node1
sudo ip link set veth_br1 master br1
sudo ip link set veth_br1 up

sudo ip link add veth_node2 type veth peer name veth_br2
sudo ip link set veth_node2 netns node2
sudo ip link set veth_br2 master br1
sudo ip link set veth_br2 up

sudo ip link add veth_node3 type veth peer name veth_br3
sudo ip link set veth_node3 netns node3
sudo ip link set veth_br3 master br2
sudo ip link set veth_br3 up

sudo ip link add veth_node4 type veth peer name veth_br4
sudo ip link set veth_node4 netns node4
sudo ip link set veth_br4 master br2
sudo ip link set veth_br4 up

# Router connections
sudo ip link add veth_router1 type veth peer name veth_br1_router
sudo ip link set veth_router1 netns router
sudo ip link set veth_br1_router master br1
sudo ip link set veth_br1_router up

sudo ip link add veth_router2 type veth peer name veth_br2_router
sudo ip link set veth_router2 netns router
sudo ip link set veth_br2_router master br2
sudo ip link set veth_br2_router up

# Assign IP addresses
sudo ip netns exec node1 ip addr add 172.0.0.2/24 dev veth_node1
sudo ip netns exec node1 ip link set veth_node1 up
sudo ip netns exec node2 ip addr add 172.0.0.3/24 dev veth_node2
sudo ip netns exec node2 ip link set veth_node2 up
sudo ip netns exec node3 ip addr add 10.10.0.2/24 dev veth_node3
sudo ip netns exec node3 ip link set veth_node3 up
sudo ip netns exec node4 ip addr add 10.10.0.3/24 dev veth_node4
sudo ip netns exec node4 ip link set veth_node4 up

sudo ip netns exec router ip addr add 172.0.0.1/24 dev veth_router1
sudo ip netns exec router ip link set veth_router1 up
sudo ip netns exec router ip addr add 10.10.0.1/24 dev veth_router2
sudo ip netns exec router ip link set veth_router2 up

# Set default gateways
sudo ip netns exec node1 ip route add default via 172.0.0.1
sudo ip netns exec node2 ip route add default via 172.0.0.1
sudo ip netns exec node3 ip route add default via 10.10.0.1
sudo ip netns exec node4 ip route add default via 10.10.0.1

# Enable IP forwarding on the router
sudo ip netns exec router sysctl -w net.ipv4.ip_forward=1