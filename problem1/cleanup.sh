# Delete namespaces
sudo ip netns delete node1
sudo ip netns delete node2
sudo ip netns delete node3
sudo ip netns delete node4
sudo ip netns delete router

# Delete bridges
sudo ip link delete br1
sudo ip link delete br2