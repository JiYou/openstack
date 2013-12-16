Swift Object Storage Service

============================

Installation steps:

For proxy node:

1 ./init.sh
2 change localrc acording your host IP etc.
3 ./swift.sh


For storage node:
1 ./init.sh
2 copy loclarc from proxy node.
3 ./swift-storage.sh  # You'd better prepare /dev/vdb as your storage disk.


