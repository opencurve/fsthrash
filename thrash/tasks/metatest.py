# -*- coding: utf-8 -*-
import os
import random
import string
import sys
import threading

import logging
import time
import pipes
import re
import shlex


from thrash import misc
from thrash.parallel import parallel

log = logging.getLogger(__name__)

def task(ctx, config):
    """
    example::
        tasks:
        - metatest:
            clients:
              dir.1:
                num_threads:10
                num_operations:10000
                num_files:10000
                max_depth:5
                 

    """
    try:
        timeout = config.get('timeout', '3h')
        log.info("ctx is %s,config is %s"%(ctx,config))
        dir_list = {}
        testdir = ctx['testdir']
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
    except:
        raise
    log.info('**************************************************')
    log.info('Started task test -- %s' % ctx['summary']['description'])
    log.info('**************************************************')
#    with parallel() as p:
#        for role, cfg in clients.items():
#            p.spawn(_run_training, ctx, role, cfg,
#                        basedir=ctx.get('basedir','workunits'),
#                        testpath=dir_list[role],
#                        timeout=timeout)
    try:
        for role, cfg in clients.items():
            _run_metatest(ctx, role, cfg,basedir=ctx.get('basedir','workunits'),testpath=dir_list[role])
    except Exception as e:
        print "程序出错: {e}".format(e=e)
        sys.exit(1)

def random_string(length):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def create_file(directory, filename, content):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(os.path.join(directory, filename), 'w') as f:
            f.write(content)
    except Exception as e:
        print "创建文件出错: {e}".format(e=e)
        sys.exit(1)

def delete_file(filepath):
    try:
        os.remove(filepath)
    except Exception as e:
        print "删除文件出错: {e}".format(e=e)
        sys.exit(1)

def read_file(filepath):
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except Exception as e:
        print "读取文件出错: {e}".format(e=e)
        sys.exit(1)

def rename(src, dst):
    try:
        os.rename(src, dst)
    except Exception as e:
        print "重命名出错: {e}".format(e=e)
        sys.exit(1)

def create_symlink(src, dst):
    try:
        if not os.path.exists(os.path.dirname(dst)):
            os.makedirs(os.path.dirname(dst))
        with open(src, 'w') as f:
            f.write('source file for symlink')
        os.system("ln -s {src} {dst}".format(src=src, dst=dst))
    except Exception as e:
        print "创建软链接出错: {e}".format(e=e)
        sys.exit(1)

def create_hardlink(src, dst):
    try:
        if not os.path.exists(os.path.dirname(dst)):
            os.makedirs(os.path.dirname(dst))
        with open(src,'w') as f:
            f.write('source file for hardlink')
        os.system("ln {src} {dst}".format(src=src, dst=dst))
    except Exception as e:
        print "创建硬链接出错: {e}".format(e=e)
        sys.exit(1)

def perform_operations(mount_points, num_operations, num_files, max_depth):
    for _ in range(num_operations):
        mount_point = random.choice(mount_points)
        depth = random.randint(1, max_depth)
        subdir = os.path.join(mount_point, *(random_string(5) for _ in range(depth)))
        operation = random.choice(['create', 'delete', 'read', 'rename', 'mkdir', 'rmdir', 'symlink', 'hardlink', 'delete_link', 'test_stat', 'create_fifo', 'list_dir'])
        if operation == 'create' or operation == 'delete' or operation == 'read':
            filename = random_string(10)
            if operation == 'create':
                create_file(subdir, filename, random_string(100))
            elif operation == 'delete':
                filepath = os.path.join(subdir, filename)
                if os.path.exists(filepath):
                    delete_file(filepath)
            elif operation == 'read':
                filepath = os.path.join(subdir, filename)
                if os.path.exists(filepath):
                    _ = read_file(filepath)
        elif operation == 'rename':
            old_name = random_string(10)
            new_name = random_string(10)
            if random.choice([True, False]):
                old_path = os.path.join(subdir, old_name)
                new_path = os.path.join(subdir, new_name)
                if os.path.exists(old_path):
                    rename(old_path, new_path)
            else:
                old_path = os.path.join(subdir, old_name)
                new_path = os.path.join(subdir, new_name)
                if os.path.exists(old_path):
                    rename(old_path, new_path)
        elif operation == 'mkdir' or operation == 'rmdir':
            dir_name = random_string(10)
            if operation == 'mkdir':
                try:
                    os.makedirs(os.path.join(subdir, dir_name))
                except OSError as e:
                    if e.errno != 17: # ignore "File exists" error
                        print "创建目录出错: {e}".format(e=e)
                        sys.exit(1)
            else:
                dir_path = os.path.join(subdir, dir_name)
                if os.path.exists(dir_path):
                    try:
                        os.rmdir(dir_path)
                    except Exception as e:
                        print "删除目录出错: {e}".format(e=e)
                        sys.exit(1)
        elif operation == 'symlink':
            src = os.path.join(subdir, "{}_source".format(random_string(10)))
            dst = os.path.join(subdir, "{}_link".format(random_string(10)))
            create_symlink(src, dst)
        elif operation == 'hardlink':
            src = os.path.join(subdir, random_string(10))
            dst = os.path.join(subdir, random_string(10))
            create_hardlink(src, dst)
        elif operation == 'delete_link':
            link_name = random_string(10)
            link_path = os.path.join(subdir, link_name)
            if os.path.exists(link_path):
                try:
                    os.remove(link_path)
                except Exception as e:
                    print "删除链接出错: {e}".format(e=e)
                    sys.exit(1)
        elif operation == 'test_stat':
            name = random_string(10)
            path = os.path.join(subdir, name)
            if os.path.exists(path):
                try:
                    st = os.stat(path)
                    if os.path.isdir(path):
                        if st.st_nlink != len(os.listdir(path)) + 2:
                            print "目录 {path} 的链接数不正确".format(path=path)
                    else:
                        if st.st_nlink != 1:
                            print "文件 {path} 的链接数不正确".format(path=path)
                except Exception as e:
                    print "stat失败: {e}".format(e=e)
                    sys.exit(1)
        elif operation == 'create_fifo':
            name = random_string(10)
            path = os.path.join(subdir, name)
            try:
                os.makedirs(os.path.dirname(path))
                os.mkfifo(path)
            except Exception as e:
                print "创建管道文件失败: {e}".format(e=e)
                sys.exit(1)
        elif operation == 'list_dir':
            dir_name = random_string(10)
            dir_path = os.path.join(subdir, dir_name)
            if os.path.exists(dir_path):
                try:
                    entries = os.listdir(dir_path)
                    expected_entries = set()
                    for _ in range(num_files):
                        expected_entries.add(random_string(10))
                    for entry in entries:
                        if entry not in expected_entries:
                            print "目录 {dir_path} 中存在不应存在的文件或目录 {entry}".format(dir_path=dir_path, entry=entry)
                    for entry in expected_entries:
                        if entry not in entries:
                            print "目录 {dir_path} 中缺少文件或目录 {entry}".format(dir_path=dir_path, entry=entry)
                except Exception as e:
                    print "listdir失败: {e}".format(e=e)
                    sys.exit(1)

def test_metadata_consistency(mount_points, num_threads, num_operations, num_files, max_depth):
    threads = []

    for _ in range(num_threads):
        t = threading.Thread(target=perform_operations, args=(mount_points, num_operations, num_files, max_depth))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print("元数据一致性测试完成")

def _run_metatest(ctx, role, cfg,basedir,testpath):
    try:
        log.info("元数据一致性测试开始")
        cmd = 'rm -rf {testpath}/metatest'.format(testpath=testpath)
        misc.sh(cmd)
        point = [testpath]
        log.info("cfg type is %s"%type(cfg))
        mount_points = cfg.get('mult_points',point)
        log.info("mount_points is %s"%mount_points)
        for index,m in enumerate(mount_points):
            mount_points[index] = m + '/metatest'
        cmd = 'mkdir {testpath}/metatest'.format(testpath=testpath)
        log.info("1111111111")
        num_threads = cfg.get('num_threads')
        log.info("num_threadsis %s"%num_threads)
        num_operations = cfg.get('num_operations')
        num_files = cfg.get('num_files')
        max_depth = cfg.get('max_depth')
        log.info("配置成功")

        test_metadata_consistency(mount_points, num_threads, num_operations, num_files, max_depth)
    except:
        raise

