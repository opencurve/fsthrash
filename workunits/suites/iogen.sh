#!/usr/bin/env bash
set -e

echo "getting iogen"
wget https://curve-tool.nos-eastchina1.126.net/fsthrash/iogen_3.1p0.tar
sudo apt-get install groff -y
tar -xvzf iogen_3.1p0.tar
cd iogen_3.1p0
echo "making iogen"
make
echo "running iogen"
./iogen -n 5 -s 2g
echo "sleep for 10 min"
sleep 600
echo "stopping iogen"
./iogen -k

echo "OK"
