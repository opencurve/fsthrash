#!/usr/bin/env bash

set -e

wget https://curve-tool.nos-eastchina1.126.net/fsthrash/pjdtest.tar.gz
tar zxvf pjdtest.tar.gz
cd pjdfstest-master
autoreconf -ifs
./configure
make pjdfstest
cd ..
mkdir tmp
cd tmp
# must be root!
sudo prove -r -v --exec 'bash -x' ../pjdfs*/tests
cd ..
rm -rf tmp pjd*
