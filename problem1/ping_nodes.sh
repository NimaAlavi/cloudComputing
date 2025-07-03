SOURCE_NODE=$1
DEST_NODE=$2

if [ -z "$SOURCE_NODE" ] || [ -z "$DEST_NODE" ]; then
    echo "Usage: ./ping_nodes.sh <source_node_name> <destination_node_name_or_ip>"
    exit 1
fi

# Example: How to get the IP of the destination node/router if needed
# You might need to hardcode IPs or have a way to resolve them based on names.
# For simplicity, let's assume DEST_NODE can be an IP directly.
# If DEST_NODE is "router", you'll ping 172.0.0.1 or 10.10.0.1 based on source_node's subnet.

# A more robust script would resolve the IP based on the name, for this example,
# let's assume we are passing the IP or the script has internal knowledge.

if [ "$SOURCE_NODE" == "node1" ]; then
    if [ "$DEST_NODE" == "router" ]; then
        sudo ip netns exec node1 ping 172.0.0.1
    elif [ "$DEST_NODE" == "node2" ]; then
        sudo ip netns exec node1 ping 172.0.0.3
    elif [ "$DEST_NODE" == "node3" ]; then
        sudo ip netns exec node1 ping 10.10.0.2 # This will go via router
    elif [ "$DEST_NODE" == "node4" ]; then
        sudo ip netns exec node1 ping 10.10.0.3 # This will go via router
    else
        echo "Invalid destination for node1"
    fi
# Add similar blocks for node2, node3, node4, and router as source
elif [ "$SOURCE_NODE" == "router" ]; then
    if [ "$DEST_NODE" == "node1" ]; then
        sudo ip netns exec router ping 172.0.0.2
    # ... and so on for other nodes
    else
        echo "Invalid destination for router"
    fi
else
    echo "Invalid source node"
fi