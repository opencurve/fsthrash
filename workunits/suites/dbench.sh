#!/usr/bin/env bash

set -e
wget https://curve-tool.nos-eastchina1.126.net/fsthrash/dbench-master.zip
unzip -o dbench-master.zip
pushd dbench-master
wget https://curve-tool.nos-eastchina1.126.net/fsthrash/dbench
chmod +x dbench
./dbench --loadfile=loadfiles/client.txt -t 300 1
./dbench --loadfile=loadfiles/client.txt -t 300 10
popd
