#!/bin/bash
set -ex
pushd ..
wget https://curve-tool.nos-eastchina1.126.net/fsthrash/ltp-full-20210524-curve.tar.bz2
tar -xvf ltp-full-20210524-curve.tar.bz2
cd ltp-full-20210524
./configure
make all
sudo make install
popd
PWD=$(pwd)
system_version=$(echo "$(uname -r)" | awk -F. '{ print $1"."$2 }')

if (( $(echo "$system_version > 5.04" | bc -l) )); then
    # 继续执行
    echo "系统版本大于5.4，执行syscalls"
    sudo /opt/ltp/runltp -d ${PWD} -f fs_bind,fs_perms_simple,fsx,io,smoketest,fs-cfs,syscalls-cfs
else
    echo "系统版本小于或等于5.4，不执行syscalls"
    sudo /opt/ltp/runltp -d ${PWD} -f fs_bind,fs_perms_simple,fsx,io,smoketest,fs-cfs
fi

# 查找目录/opt/ltp/results/下最新修改时间的文件
file=$(find /opt/ltp/results/ -type f -printf "%T@ %p\n" | sort -n | tail -n 1 | awk '{print $2}')

# 搜索文件中的“Total Failures:”字段并提取其中的0值
failures=$(grep "Total Failures:" "$file" | awk '{print $NF}')

# 如果失败数量大于0，则退出脚本并返回1
if [ "$failures" -gt 0 ]; then
    echo "Failures found: $failures"
    exit 1
fi

# 如果没有找到失败，则退出脚本并返回0
echo "No failures found"
exit 0
