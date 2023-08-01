#!/usr/bin/env bash

set -e
wget https://curve-tool.nos-eastchina1.126.net/fsthrash/iozone3_492.tar
tar -xvf iozone3_492.tar
pushd iozone3_492/src/current
make linux
./iozone -c -e -s 1024M -r 16K -t 1 -F f1 -i 0 -i 1
./iozone -c -e -s 1024M -r 1M -t 1 -F f2 -i 0 -i 1
./iozone -c -e -s 10240M -r 1M -t 1 -F f3 -i 0 -i 1

# basic tests of O_SYNC, O_DSYNC, O_RSYNC
# test O_SYNC
./iozone -c -e -s 512M -r 1M -t 1 -F osync1 -i 0 -i 1 -o
# test O_DSYNC
./iozone -c -e -s 512M -r 1M -t 1 -F odsync1 -i 0 -i 1 -+D
# test O_RSYNC
./iozone -c -e -s 512M -r 1M -t 1 -F orsync1 -i 0 -i 1 -+r

./iozone -a -g 1024k  –i 0 –i 1 –i 2 –i 3 –i 4 –i 5 –i 8 –t 8 > result.xls
./iozone -a -g 1g 4m  –i 0 –i 1 –i 2 –i 3 –i 4 –i 5 –i 8 –t 8 > result.xls

popd
