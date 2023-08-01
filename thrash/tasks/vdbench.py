import json
import logging
import os
import re

#from thrash.parallel import parallel
from tempfile import NamedTemporaryFile
from thrash import misc
from thrash import mythread

log = logging.getLogger(__name__)

def task(ctx, config):
    """
  vdbench:
    clients:
      dir.1:
        depth: 1
        width: 10
        files: 10
        size: 100m
        threads: 10
        xfersize: (512,20,4k,20,64k,20,512k,20,1024k,20)
        rdpct: 50
        elapsed: 600
      dir.2:
        depth: 1
        width: 10
        files: 10
        size: 100m
        threads: 10
        xfersize: (512,20,4k,20,64k,20,512k,20,1024k,20)
    """
    if config.get('all'):
        client_config = config['all']
    dir_list = {}
    testdir = ctx['testdir']
    try:
        i = 1
        for t in testdir:
            dir_name = 'dir.' + str(i)
            dir_list[dir_name] = t
            i += 1
        log.info("ctx testdir is %s"%testdir)
        log.info('dir_list is  %s', dir_list)
        clients = config['clients']
        log.info("clients is %s"%clients)
        for role in clients.keys():
            assert isinstance(role, str)
            log.info("role is %s"%role)
            if role == "all":
                continue
    except Exception:
        log.error('get clients yaml config fail')
        raise
    if not os.path.exists('./vdbench'):
        get_vdbench_tool('vdbench50407.tar.gz')
    threads_list = []
    for role, tests in clients.items():
        thread = mythread.runThread(run_vdbench,role,tests,dir_list[role])
        thread.start()
        threads_list.append(thread)
    for t in threads_list:
        t.get_result()

def get_vdbench_tool(pkg):
    cmd = "wget https://curve-tool.nos-eastchina1.126.net/fsthrash/{vdbench} -O {vdbench}".format(vdbench=pkg)
    misc.sh(cmd)
    cmd = 'tar -xvf {vdbench}'.format(vdbench=pkg)
    misc.sh(cmd)

def alter(file1,file2,data):
    log.info("data is %s",data)
    newdata = []
    with open(file1, "r") as f1,open(file2, "w") as f2:
        for l in f1.readlines():
           newdata.append(l)
        f1.close()
        for k in data.keys():
            if k == 'xfersize':
                for i,line in enumerate(newdata):
                    if k in line:
                        newdata[i] = re.sub('(?<='+k+'=)\(\S+\)',str(data[k]),line)
                         
            else:
                for i,line in enumerate(newdata):
                    if k in line:
                        newdata[i] = re.sub('(?<='+k+'=)\w+',str(data[k]),line)
        f2.writelines(newdata)
        f2.close()

def run_vdbench(role, tests, anchor, timeout=None):
    """
    create vdbench config file with options based on above config
    """
    vdbench_path = "./vdbench/"
    profile_path = vdbench_path + "profile_" + role
    tests['anchor'] = anchor
    output_path = vdbench_path + 'output_' + role
    alter('tools/vdbench.template',profile_path,tests)
    try:
        log.info("Running vdbench feature - vdbench test on {sn}".format(sn=anchor))
        cmd = "cd " + vdbench_path + " && " + "./vdbench -f "  \
             + os.path.abspath(profile_path) + " -jn" + " -o " + os.path.abspath(output_path)
        log.info("cmd is %s",cmd)
        misc.sh(cmd)
    finally:
        cmd = "grep \"Vdbench execution completed successfully\" {output} -R".format(output=output_path)
        check = misc.sh(cmd)
        if check:
            log.info("test pass,stopping vdbench test on anchor %s",anchor)
            return check
        else:
            log.error("vdbench test fail on %s,log is in %s",anchor,output_path)
