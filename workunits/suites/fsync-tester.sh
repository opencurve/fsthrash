#!/bin/sh -x

set -e

wget https://curve-tool.nos-eastchina1.126.net/fsthrash/fsync-tester.c
gcc -D_GNU_SOURCE fsync-tester.c -o fsync-tester

./fsync-tester

echo $PATH
whereis lsof
lsof
